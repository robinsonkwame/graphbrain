import ast
import logging
from dataclasses import dataclass
from typing import Union, Any, Callable

from spacy.language import Language
from spacy.lang.en import English
from spacy.tokens import Doc
from spacy_transformers import TransformerData
from spacy_transformers.pipeline_component import Transformer
from thinc.types import Ragged
from torch import Tensor
from torch.nn import CosineSimilarity
import torch.nn.functional as F

from graphbrain import hedge
from graphbrain.hyperedge import Hyperedge
from graphbrain.hypergraph import Hypergraph
from graphbrain.semsim.matchers.matcher import SemSimMatcher, SemSimConfig

logger: logging.Logger = logging.getLogger(__name__)


# TODO: Caching! (only for references?)
# TOOD: pass candidate edge token positions (gets rid of recursive edge search)

@dataclass
class RootEdgeAttributes:
    text: str
    tokens: list[str]
    tok_pos: Hyperedge


class ContextEmbeddingMatcher(SemSimMatcher):
    def __init__(self, config: SemSimConfig):
        super().__init__(config)
        self._spacy_trf_pipe: Language = create_spacy_pipeline(config.model_name)
        self._cos_sim: CosineSimilarity = CosineSimilarity(dim=1)

    def filter_oov(self, words: list[str]) -> list[str]:
        pass

    def _similarities(
            self,
            candidate: str,
            references: list[str],
            candidate_edge: Hyperedge = None,
            root_edge: Hyperedge = None,
            hg: Hypergraph = None,
            **kwargs
    ) -> Union[dict[str, int], None]:
        # embedding for reference(s) is missing, needs example sentences
        # TODO: pass examples: sentence, tokenization, token idx

        root_edge_attr: RootEdgeAttributes | None = get_and_validate_root_edge_attributes(root_edge, hg)
        if not root_edge_attr:
            return None

        # find out to which token idx in the root edge the candidate refers to
        candidate_tok_idx: int | None = get_and_validate_candidate_tok_idx(
            candidate, root_edge_attr.text, root_edge_attr.tokens, candidate_edge, root_edge, root_edge_attr.tok_pos
        )
        if not candidate_tok_idx:
            return None

        candidate_trf_embedding: Tensor = self.get_candidate_trf_embedding(
            root_edge_attr.text, root_edge_attr.tokens, candidate_tok_idx
        )
        reference_trf_embeddings: list[Tensor] = self.get_reference_trf_embedding(references)

        tmp = {ref: float(self._cos_sim(candidate_trf_embedding, reference_trf_embedding))
               for ref, reference_trf_embedding in zip(references, reference_trf_embeddings)}

        return tmp

    def get_candidate_trf_embedding(self, root_edge_text: str, root_edge_tokens: list[str], candidate_tok_idx: int):
        root_edge_spacy_doc: Doc = self._spacy_trf_pipe(root_edge_text)

        # check if spacy lexical tokenization equals root edge tokens
        root_edge_lexical_tokens: list[str] = spacy_doc2str_list(root_edge_spacy_doc)
        try:
            assert root_edge_lexical_tokens == root_edge_tokens
        except AssertionError:
            logger.warning(f"Spacy lexical tokenization does not equal root edge tokens: "
                           f"{root_edge_lexical_tokens=} != {root_edge_tokens=}")
            return False

        return get_trf_embedding(root_edge_tokens, candidate_tok_idx, root_edge_spacy_doc._.trf_data)  # noqa

    # TODO: adapt to handle sentences, needs additional idxes parameter
    def get_reference_trf_embedding(self, references: list[str]):
        reference_docs: list[Doc] = [self._spacy_trf_pipe(reference) for reference in references]
        references_tokens: list[list[str]] = [spacy_doc2str_list(doc) for doc in reference_docs]
        references_trf_data: list[TransformerData] = [doc._.trf_data for doc in reference_docs]  # noqa
        return [get_trf_embedding(tokens, 0, trf_data) for tokens, trf_data
                in zip(references_tokens, references_trf_data)]


def get_and_validate_root_edge_attributes(root_edge: Hyperedge, hg: Hypergraph) -> RootEdgeAttributes | None:
    root_edge_text: str = hg.text(root_edge)
    root_edge_tokens: list[str] | None = get_and_validate_root_edge_str_attribute(
        'tokens', root_edge, hg, constructor=ast.literal_eval
    )
    root_edge_tok_pos: Hyperedge | None = get_and_validate_root_edge_str_attribute(
        'tok_pos', root_edge, hg, constructor=hedge
    )

    # root edge is not a full sentence (sequence)
    if not root_edge_tokens or not root_edge_tok_pos:
        return None

    # if len(root_edge_tokens) != len(root_edge.atoms()):
    #     logger.warning(f"Root edge token number does not equal number of atoms: "
    #                    f"{len(root_edge_tokens)=} != {len(root_edge.atoms())=}, "
    #                    f"{root_edge_tokens=}, {root_edge.atoms()=}")
    #     return None

    return RootEdgeAttributes(text=root_edge_text, tokens=root_edge_tokens, tok_pos=root_edge_tok_pos)


def get_and_validate_root_edge_str_attribute(
        attribute_name: str, root_edge: Hyperedge, hg: Hypergraph, constructor: Callable
) -> Any:
    attribute_str_val: str = hg.get_str_attribute(root_edge, attribute_name)
    if not attribute_str_val:
        return None
    try:
        attribute_val: Any = constructor(attribute_str_val)
    except ValueError:
        logger.error(f"Root edge has invalid '{attribute_name}' attribute: {attribute_str_val}")
        return None
    return attribute_val


def get_and_validate_candidate_tok_idx(
        candidate: str,
        root_edge_text: str,
        root_edge_tokens: list[str],
        candidate_edge: Hyperedge,
        root_edge: Hyperedge,
        root_edge_tok_pos: Hyperedge
) -> int | None:
    candidate_tok_idx: int | None = get_candidate_tok_idx(candidate_edge, root_edge, root_edge_tok_pos)
    if candidate_tok_idx is None:
        logger.warning(f"No token idx found in '{root_edge_text}' "
                       f"for candidate: '{candidate}' (edge: {candidate_edge})")
        return None

    # check if corresponding token equals the given candidate str
    candidate_token: str = root_edge_tokens[candidate_tok_idx]
    try:
        assert candidate.lower() == candidate_token.lower()
    except AssertionError:
        logger.warning(f"Token in root edge does not equal candidate: "
                       f"'{candidate_token}' (idx: {candidate_tok_idx}) != '{candidate}'. "
                       f"Root edge tokens: {root_edge_tokens}")
        return None

    return candidate_tok_idx


def get_candidate_tok_idx(candidate_edge: Hyperedge, root_edge: Hyperedge, root_edge_tok_pos: Hyperedge) -> int | None:
    # candidate_edge = graphbrain.hyperedge.unique(candidate_edge)
    # root_edge = graphbrain.hyperedge.unique(root_edge)

    candidate_edge_location: list[int] | None = recursive_edge_search(root_edge, candidate_edge)
    if not candidate_edge_location:
        return None

    candidate_edge_tok_pos: Hyperedge = hedge(root_edge_tok_pos)
    for idx in candidate_edge_location:
        try:
            candidate_edge_tok_pos: Hyperedge = candidate_edge_tok_pos[idx]
        except IndexError:
            return None

    return int(candidate_edge_tok_pos[0])


# based on atom string equality, DOES NOT WORK IN CASES WITH IDENTICAL SUB-EDGES! TODO: fix it!
def recursive_edge_search(
        current_edge: Hyperedge,
        candidate_edge: Hyperedge,
        edge_location: list[int] = None
) -> list[int] | None:
    if not edge_location:
        edge_location = []
    if current_edge.atom:
        # if current_edge[0] == candidate_edge[0]:
        if current_edge == candidate_edge:
            return edge_location
        return None
    for sub_edge_idx, sub_edge in enumerate(current_edge):
        if sub_edge_location := recursive_edge_search(sub_edge, candidate_edge, [sub_edge_idx]):
            return edge_location + sub_edge_location
    return None


def create_spacy_pipeline(model_name: str) -> Language:
    nlp: Language = English()
    config = {
        "model": {
            "@architectures": "spacy-transformers.TransformerModel.v3",
            "name": model_name,
            "tokenizer_config": {"use_fast": True},
        }
    }
    trf: Transformer = nlp.add_pipe("transformer", config=config)  # noqa
    trf.model.initialize()
    return nlp


def spacy_doc2str_list(spacy_doc: Doc):
    return [tok.text for tok in spacy_doc]


def get_trf_embedding(lexical_tokens: list[str], tok_idx: int, trf_data: TransformerData) -> Tensor:
    tok_trf_idxes: list[int] = get_lex2trf_idx(lexical_tokens, trf_data.align)[tok_idx]
    trf_tokens: list[str] = [trf_data.wordpieces.strings[0][tok_idx] for tok_idx in tok_trf_idxes]

    logger.debug(f"LEX token: {lexical_tokens[tok_idx]}, TRF tokens: {trf_tokens}")

    candidate_trf_embeddings: Tensor = Tensor(trf_data.model_output.last_hidden_state[:, tok_trf_idxes, :])
    return average_pool(candidate_trf_embeddings, Tensor(trf_data.wordpieces.attention_mask[:, tok_trf_idxes]))


# Adapted from: https://huggingface.co/intfloat/e5-base
def average_pool(last_hidden_states: Tensor, attention_mask: Tensor, normalize: bool = False) -> Tensor:
    last_hidden: Tensor = last_hidden_states.masked_fill(~attention_mask[..., None].bool(), 0.0)
    embeddings: Tensor = last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]
    if normalize:
        embeddings = F.normalize(embeddings, p=2, dim=1)
    return embeddings


# Make alignment between lexical tokens and transformer (sentencepiece, wordpiece, ...) tokens
def get_lex2trf_idx(lexical_tokens: list[str], alignment_data: Ragged) -> dict[int, list[int]]:
    lex2trf_idx: dict[int, list[int]] = {}
    trf_idx: int = 0
    for lex_idx in range(len(lexical_tokens)):
        trf_token_length: int = alignment_data.lengths[lex_idx]
        lex2trf_idx[lex_idx] = list(alignment_data.dataXd[trf_idx:trf_idx + trf_token_length])
        trf_idx += trf_token_length
    return lex2trf_idx

# def get_lex2trf_idx(lexical_tokens: list[str], alignment_data: Ragged) -> dict[int, list[int]]:
#     return {lex_idx: get_trf_token_idxes(lex_idx, alignment_data) for lex_idx in range(len(lexical_tokens))}

# def get_trf_token_idxes(lex_idx_: int, alignment_data: Ragged):
#     start_idx: int = int(np.sum(alignment_data.lengths[:lex_idx_]))
#     end_idx: int = start_idx + alignment_data.lengths[lex_idx_]
#     return alignment_data.dataXd[start_idx:end_idx]

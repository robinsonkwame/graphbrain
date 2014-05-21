(ns graphbrain.braingenerators.wordnet
  (:require [graphbrain.db.gbdb :as gb]
            [graphbrain.db.id :as id]
            [graphbrain.db.maps :as maps]
            [graphbrain.db.text :as text])
  (:import (org.w3c.dom ElementTraversal)
           (net.sf.extjwnl.data PointerUtils
                                POS)
           (net.sf.extjwnl.data.list PointerTargetNode
                                     PointerTargetNodeList)
           (net.sf.extjwnl.dictionary Dictionary)
           (java.io FileInputStream)
           (java.security NoSuchAlgorithmException)))

(def dryrun false)

(defn add-relation!
  [gbdb rel]
  (prn (str "rel: " rel))
  (if (not dryrun) (gb/putv! gbdb (maps/id->edge rel) "c/wordnet")))

(defn super-type
  [word]
  (let [concept (.getSynset word)
        hypernyms (PointerUtils/getDirectHypernyms concept)]
    (if (not (empty? hypernyms))
        (let [hypernym (.getFirst hypernyms)]
          (if hypernym
            (first (.getWords (.getSynset hypernym))))))))

(defn example
  [word]
  (let [synset (.getSynset word)
        example (.getGloss synset)]
    (text/text->vertex example)))

(defn vertex-id
  [word]
  (let [id (id/sanitize (.getLemma word))]
    (if (= id "entity") id
        (let [st (super-type word)
              rel (if st
                    (str "(r/+type_of " id " " (vertex-id st) ")")
                    (let [tn (example word)]
                      (str "(r/+example " id " " (:id tn) ")")))]
          (str (id/hashed rel) "/" id)))))

(defn process-super-types!
  [gbdb vid word]
  (let [concept (.getSynset word)
        hypernyms (PointerUtils/getDirectHypernyms concept)]
    (doseq [hypernym hypernyms]
      (let [super-word (first (.getWords (.getSynset hypernym)))
            super-id (vertex-id super-word)
            rel (str "(r/+type_of " vid " " super-id ")")]
        (add-relation! gbdb rel)))))

(defn process-synonyms!
  [gbdb synset]
  (let [word-list (.getWords synset)
        main-word (nth word-list 0)
        vid (vertex-id main-word)]
    (doseq [syn word-list]
      (let [syn-id (vertex-id syn)
            rel (str "(r/+synonym " vid " " syn-id ")")]
        (if (not (= vid syn-id))
                 (add-relation! gbdb rel))))))

(defn process-meronyms!
  [gbdb vid word]
  (let [concept (.getSynset word)
        results (PointerUtils/getMeronyms concept)]
    (doseq [result results]
      (let [part-word (first (.getWords (.getSynset result)))
            part-id (vertex-id part-word)
            rel (str "(r/+part_of " part-id " " vid ")")]
        (add-relation! gbdb rel)))))

(defn process-antonyms!
  [gbdb vid word]
  (let [concept (.getSynset word)
        results (PointerUtils/getAntonyms concept)]
    (doseq [result results]
      (let [ant-word (first (.getWords (.getSynset result)))
            ant-id (vertex-id ant-word)
            rel (str "(r/+antonym " vid " " ant-id ")")]
        (add-relation! gbdb rel)))))

(defn process-also-sees!
  [gbdb vid word]
  (let [concept (.getSynset word)
        results (PointerUtils/getAlsoSees concept)]
    (doseq [result results]
      (let [also-word (first (.getWords (.getSynset result)))
            also-id (vertex-id also-word)
            rel (str "(r/+also_see " vid " " also-id ")")]
        (add-relation! gbdb rel)))))

(defn process-can-mean!
  [gbdb vid word]
  (if (super-type word)
    (let [sid (id/sanitize (.getLemma word))
          rel (str "(r/+can_mean " sid " " vid ")")]
      (add-relation! gbdb rel))))

(defn process-pos!
  [gbdb vid word]
  (let [pos (.getPOS word)]
    (if pos
      (let [pos-id (cond
                     (.equals pos POS/NOUN) "850e2accee28f70e/noun"
                     (.equals pos POS/VERB) "b43b5b40bb0873e9/verb"
                     (.equals pos POS/ADJECTIVE) "90a283c76334fb9d/adjective"
                     (.equals pos POS/ADVERB) "20383f8100e0be26/adverb")
            rel (str "(r/+pos " vid " " pos-id ")")]
        (add-relation! gbdb rel)))))

(defn process-example!
  [gbdb vid word]
  (let [tn (example word)]
    (if (not dryrun) (gb/putv! gbdb tn))
    (let [rel (str "(r/+example " vid " " (:id tn) ")")]
      (add-relation! gbdb rel))))

(defn process-synset!
  [gbdb synset]
  (process-synonyms! gbdb synset)
  (let [main-word (first (.getWords synset))
        mwid (vertex-id main-word)]
    (process-meronyms! gbdb mwid main-word)
    (process-antonyms! gbdb mwid main-word)
    (process-also-sees! gbdb mwid main-word)
    (process-example! gbdb mwid main-word)
    (let [words (.getWords synset)]
          (doseq [word words]
            (let [vid (vertex-id word)]
              (prn vid)
              (process-can-mean! gbdb vid word)
              (process-super-types! gbdb vid word)
              (process-pos! gbdb vid word))))))

(defn process-pos-synset!
  [gbdb dictionary pos]
  (let [iter (.getSynsetIterator dictionary pos)]
    (while (.hasNext iter)
      (let [synset (.next iter)]
        (prn synset)
        (process-synset! gbdb synset)))))

(defn process!
  [gbdb dictionary]
  (gb/create-user! gbdb "wordnet" "wordnet" "" "" "crawler")
  (process-pos-synset! gbdb dictionary (POS/NOUN))
  (process-pos-synset! gbdb dictionary (POS/VERB))
  (process-pos-synset! gbdb dictionary (POS/ADJECTIVE))
  (process-pos-synset! gbdb dictionary (POS/ADVERB)))

(defn run!
  []
  (let [dictionary (Dictionary/getDefaultResourceInstance)
        gbdb (gb/gbdb)]
    (process! gbdb dictionary)))

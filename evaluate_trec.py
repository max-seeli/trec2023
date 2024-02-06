import argparse
parser = argparse.ArgumentParser(description='Takes a run and calculates the appropriate TREC metrics for the 2023 qrels.')

parser.add_argument('run_file', type=str, help='Input the path of your run file.')

args = parser.parse_args()

import pyterrier as pt
import pandas as pd

if not pt.started():
    pt.init()

class DummyRetriever(pt.transformer.TransformerBase):
    def __init__(self, results_df):
        self.results_df = results_df

    def transform(self, topics):
        return self.results_df

qrels_df = pt.io.read_qrels("./data/new_qrels/2023-qrels.txt")
binary_qrels_df = pt.io.read_qrels("./data/new_qrels/2023-qrels-binary.txt")
run_df = pt.io.read_results(args.run_file)

unique_topics = run_df['qid'].unique() #topics no
topics_df = pd.DataFrame(unique_topics, columns=['qid'])

dummy_retriever = DummyRetriever(run_df)

results = pt.Experiment(
    [dummy_retriever],
    topics_df,
    qrels_df,
    eval_metrics=["ndcg_cut_5", "ndcg_cut_10"]
)

results_binary = pt.Experiment(
    [dummy_retriever],
    topics_df,
    binary_qrels_df,
    eval_metrics=["P_10", "recip_rank"]
)

merged_df = pd.merge(results, results_binary, on='name')

merged_df = merged_df.drop(columns=['name'])

print(merged_df)

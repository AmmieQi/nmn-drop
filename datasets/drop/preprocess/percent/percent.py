import argparse
from collections import defaultdict
import json
import os

import datasets.drop.constants as constants

PERCENT_NGRAMS = ["how many in percent"]


def readDataset(input_json):
    with open(input_json, "r") as f:
        dataset = json.load(f)
    return dataset


def prune_PercentDataset(dataset):
    """ Extract all questions that contain any one of the PERCENT_N-GRAMS """

    new_dataset = {}
    total_ques = 0
    after_pruning_ques = 0
    num_passages = len(dataset)

    qtype_dist = defaultdict(int)

    for passage_id, passage_info in dataset.items():
        new_qa_pairs = []
        for question_answer in passage_info[constants.qa_pairs]:
            total_ques += 1

            original_question = question_answer[constants.cleaned_question]
            question_lower = original_question.lower()

            if any(span in question_lower for span in PERCENT_NGRAMS):
                new_qa_pairs.append(question_answer)

        if len(new_qa_pairs) > 0:
            passage_info[constants.qa_pairs] = new_qa_pairs
            new_dataset[passage_id] = passage_info
            after_pruning_ques += len(new_qa_pairs)

    num_passages_after_prune = len(new_dataset)
    print(f"Passages original:{num_passages}  After Pruning:{num_passages_after_prune}")
    print(f"Questions original:{total_ques}  After pruning:{after_pruning_ques}")
    print(f"Qtype dict: {qtype_dist}")

    return new_dataset


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir")
    parser.add_argument("--output_dir")
    args = parser.parse_args()

    train_json = "drop_dataset_train.json"
    dev_json = "drop_dataset_dev.json"

    input_dir = args.input_dir
    output_dir = args.output_dir

    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    print(f"Output dir: {output_dir}")

    input_trnfp = os.path.join(input_dir, train_json)
    input_devfp = os.path.join(input_dir, dev_json)
    output_trnfp = os.path.join(output_dir, train_json)
    output_devfp = os.path.join(output_dir, dev_json)

    train_dataset = readDataset(input_trnfp)
    dev_dataset = readDataset(input_devfp)

    new_train_dataset = prune_PercentDataset(train_dataset)

    new_dev_dataset = prune_PercentDataset(dev_dataset)

    with open(output_trnfp, "w") as f:
        json.dump(new_train_dataset, f, indent=4)

    with open(output_devfp, "w") as f:
        json.dump(new_dev_dataset, f, indent=4)

    print("Written augmented datasets")

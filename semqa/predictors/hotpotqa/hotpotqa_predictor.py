from typing import List

from overrides import overrides

from allennlp.common.util import JsonDict, sanitize, group_by_count
from allennlp.data import DatasetReader, Instance
from allennlp.models import Model
from allennlp.predictors.predictor import Predictor
import datasets.hotpotqa.utils.constants as hpconstants
import utils.util as myutils

@Predictor.register("hotpotqa_predictor")
class HotpotQAPredictor(Predictor):
    """
    Predictor for the :class:`~allennlp.models.bidaf.SemanticRoleLabeler` model.
    """
    def __init__(self, model: Model, dataset_reader: DatasetReader) -> None:
        super().__init__(model, dataset_reader)


    @overrides
    def predict_instance(self, instance: Instance) -> JsonDict:
        outputs = self._model.forward_on_instance(instance)
        return sanitize(outputs)


    def predict_batch_instance(self, instances: List[Instance]) -> List[JsonDict]:
        outputs = self._model.forward_on_instances(instances)
        return sanitize(outputs)


    def _print_ExecutionValTree(self, exval_tree, depth):
        """
        exval_tree: [[root_func_name, value], [], [], []]
        """
        tabs = '\t' * depth
        outstr = f"{tabs}{exval_tree[0][0]}  :  {exval_tree[0][1]}\n"
        if len(exval_tree) > 1:
            for child in exval_tree[1:]:
                outstr += self._print_ExecutionValTree(child, depth+1)
        return outstr

    @overrides
    def dump_line(self, outputs: JsonDict) -> str:  # pylint: disable=no-self-use
        # Use json.dumps(outputs) + "\n" to dump a dictionary

        out_str = ''
        metadata = outputs['metadata']
        question = metadata['question']
        answer = metadata['answer']
        contexts = metadata['contexts']

        logical_forms = outputs['logical_forms']
        execution_vals = outputs['execution_vals']
        execution_vals = myutils.round_all(execution_vals, 4)
        denotations = myutils.round_all(outputs['denotations'], 4)

        out_str += f"Question: {question}\n"
        out_str += f"Answer: {answer}\n"
        if 'logical_forms' and 'denotations' in outputs:
            for lf, d, ex_vals in zip(logical_forms, denotations, execution_vals):
                # Stripping the trailing new line
                ex_vals_str = self._print_ExecutionValTree(ex_vals, 0).strip()
                out_str += f"LogicalForm: {lf}\nDenotation: {d}\nExecutionTree:\n{ex_vals_str}\n"

        out_str += "Contexts:\n"
        for c in contexts:
            out_str += f"{c}\n"
        out_str += '\n'

        # answer_num = 0.0
        # pred_num = 0.0
        #
        # if answer == 'yes':
        #     out_str += '1.0\t'
        #     answer_num = 1.0
        # else:
        #     out_str += '0.0\t'
        #
        # if denotations[0] >= 0.5:
        #     out_str += '1.0\t'
        #     pred_num = 1.0
        # else:
        #     out_str += '0.0\t'
        #
        # if answer_num == pred_num:
        #     out_str += '1.0\n'
        # else:
        #     out_str += '0.0\n'
        return out_str

    @overrides
    def _json_to_instance(self, json_dict: JsonDict):
        jsonobj = json_dict
        # space delimited tokenized
        question = jsonobj[hpconstants.q_field]

        answer = jsonobj[hpconstants.ans_field]
        # List of question mentions. Stored as mention-tuples --- (text, start, end, label)
        # TODO(nitish): Fix this to include all types
        q_nemens = jsonobj[hpconstants.q_ent_ner_field]
        # List of (title, space_delimited_tokenized_contexts)
        contexts = jsonobj[hpconstants.context_field]
        # List of list --- For each context , list of mention-tuples as (text, start, end, label)
        contexts_ent_ners = jsonobj[hpconstants.context_ent_ner_field]
        contexts_num_ners = jsonobj[hpconstants.context_num_ner_field]
        contexts_date_ners = jsonobj[hpconstants.context_date_ner_field]

        # Mention to entity mapping -- used to make the grounding vector
        context_entmens2entidx = jsonobj[hpconstants.context_entmens2entidx]
        context_nummens2entidx = jsonobj[hpconstants.context_nummens2entidx]
        context_datemens2entidx = jsonobj[hpconstants.context_datemens2entidx]

        # Entity to mentions --- Used to find the number of entities of each type in the contexts
        context_eqent2entmens = jsonobj[hpconstants.context_eqent2entmens]
        context_eqent2nummens = jsonobj[hpconstants.context_eqent2nummens]
        context_eqent2datemens = jsonobj[hpconstants.context_eqent2datemens]

        # Dict from {date_string: (date, month, year)} normalization. -1 indicates invalid field
        dates_normalized_dict = jsonobj[hpconstants.dates_normalized_field]
        # Dict from {num_string: float_val} normalization.
        nums_normalized_dict = jsonobj[hpconstants.nums_normalized_field]
        # Dict from {ent_idx: [(context_idx, men_idx)]} --- output pf CDCR

        # Grounding of ques entity mentions
        qnemens_to_ent = jsonobj[hpconstants.q_entmens2entidx]

        ans_type = None
        ans_grounding = None
        # if hpconstants.ans_type_field in jsonobj:
        #     ans_type = jsonobj[hpconstants.ans_type_field]
        #     ans_grounding = jsonobj[hpconstants.ans_grounding_field]

        instance = self._dataset_reader.text_to_instance(question,
                                                         answer,
                                                         q_nemens,
                                                         contexts,
                                                         contexts_ent_ners,
                                                         contexts_num_ners,
                                                         contexts_date_ners,
                                                         context_entmens2entidx,
                                                         context_nummens2entidx,
                                                         context_datemens2entidx,
                                                         context_eqent2entmens,
                                                         context_eqent2nummens,
                                                         context_eqent2datemens,
                                                         dates_normalized_dict,
                                                         nums_normalized_dict,
                                                         qnemens_to_ent,
                                                         ans_type,
                                                         ans_grounding)
        return instance

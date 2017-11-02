import argparse
from os import makedirs
from os.path import exists, join

from common.imp_arg import ImplicitArgumentDataset
from config import cfg
from model.imp_arg_logit.classifier import BinaryClassifier
from utils import add_file_handler, log

parser = argparse.ArgumentParser()
parser.add_argument('--use_list', action='store_true',
                    help='if turned on, the p_1_word / p_2_word / p_3_word '
                         'features would be created as a list rather than '
                         'concatenation')
parser.add_argument('--featurizer', default='one_hot',
                    help='the featurizer to transform all features,'
                         'one_hot (default) or hash')
parser.add_argument('--fit_intercept', action='store_true',
                    help='if turned on, the logistic regression model '
                         'would add a constant intercept (1) to the '
                         'decision function')
parser.add_argument('--tune_w', action='store_true',
                    help='if turned on, the logistic regression model '
                         'would search for best class_weight parameter, '
                         'otherwise class_weight is set to balanced')
parser.add_argument('--use_val', action='store_true',
                    help='if turned on, in cross validation a separate '
                         'fold would be used as validation set, otherwise '
                         'all training folds would be used for validation')
parser.add_argument('--verbose', action='store_true',
                    help='if turned on, evaluation results on every '
                         'parameter grid on every fold would be printed')
parser.add_argument('--log_to_file', action='store_true',
                    help='if turned on, logs would be written to file')
parser.add_argument('--save_results', action='store_true',
                    help='if turned on, results would be written to file')
parser.add_argument('--save_models', action='store_true',
                    help='if turned on, all trained models would be saved')
parser.add_argument('--predict_missing_labels', action='store_true',
                    help='if turned on, a dictionary of predicted '
                         'missing labels would be saved')

args = parser.parse_args()

if args.use_list:
    path_prefix = join(
        cfg.data_path, 'imp_arg_logit', 'binary_classifier', 'list_features')
else:
    path_prefix = join(
        cfg.data_path, 'imp_arg_logit', 'binary_classifier', 'concat_features')

if not exists(path_prefix):
    makedirs(path_prefix)

suffix = '{}-{}-{}-{}'.format(
    args.featurizer,
    'intercept' if args.fit_intercept else 'no_intercept',
    'tune_weight' if args.tune_w else 'balanced_weight',
    'use_val' if args.use_val else 'use_train')

if args.log_to_file:
    log_file_path = join(path_prefix, 'log-{}.log'.format(suffix))

    add_file_handler(log, log_file_path)

classifier = BinaryClassifier(n_splits=10)

dataset = ImplicitArgumentDataset()
classifier.read_dataset(dataset)

sample_list_path = join(path_prefix, 'sample_list.pkl')
if exists(sample_list_path):
    classifier.load_sample_list(sample_list_path)
else:
    classifier.build_sample_list(
        use_list=args.use_list, save_path=sample_list_path)

classifier.index_sample_list()

classifier.preprocess_features(args.featurizer)

classifier.set_hyper_parameter(
    fit_intercept=args.fit_intercept, tune_w=args.tune_w)

classifier.cross_validation(use_val=args.use_val, verbose=args.verbose)

fout_results = None
if args.save_results:
    results_path = join(path_prefix, 'results-{}.txt'.format(suffix))
    fout_results = open(results_path, 'w')

classifier.print_stats(fout=fout_results)

if args.save_models:
    model_save_path = join(path_prefix, 'model-{}.pkl'.format(suffix))
    classifier.save_models(model_save_path)

if args.predict_missing_labels:
    missing_labels_save_path = join(
        path_prefix, 'missing_labels-{}.pkl'.format(suffix))

    classifier.predict_missing_labels(save_path=missing_labels_save_path)
import pandas as pd
import numpy as np
import sklearn.metrics as skmetrics
from sklearn import svm
from sklearn import linear_model
from sklearn.linear_model import LinearRegression
from sklearn.feature_selection import RFE
from sklearn.linear_model import Lasso

np.random.seed(seed=149)
# from sklearn.metrics import classification_report, confusion_matrix

# ---------------------------------------------------------
# ------------ DATA IMPORT AND DEFINITIONS ----------------
# ---------------------------------------------------------

# cleaned data import:
train_features = pd.read_csv("../data/train_features_clean_columned.csv")
test_features = pd.read_csv("../data/test_features_clean_columned.csv")
train_labels = pd.read_csv("../data/train_labels.csv")
sample = pd.read_csv("../sample.csv")
stored_usefulness_matrix_t1 = pd.read_csv("../data/usefulness_matrix_t1_dummy.csv")
stored_usefulness_matrix_t3 = pd.read_csv("../data/usefulness_matrix_t3_dummy.csv")

# features
patient_characteristics = ["Age"]  # TIME VARIABLE IS EXCLUDED
vital_signs = ["Heartrate", "SpO2", "ABPs", "ABPm", "ABPd", "RRate", 'Temp']
tests = ['EtCO2', 'PTT', 'BUN', 'Lactate', 'Hgb', 'HCO3', 'BaseExcess',
       'Fibrinogen', 'Phosphate', 'WBC', 'Creatinine', 'PaCO2', 'AST', 'FiO2',
       'Platelets', 'SaO2', 'Glucose', 'Magnesium', 'Potassium', 'Calcium',
       'Alkalinephos', 'Bilirubin_direct', 'Chloride', 'Hct',
       'Bilirubin_total', 'TroponinI', 'pH']
all_features = patient_characteristics + vital_signs + tests
N_hours = 12
houred_features = patient_characteristics + sum(
    [[houred_feature + str(i) for i in range(13 - N_hours, 13)] for houred_feature
     in (vital_signs + tests)], [])

# labels
labels_tests = ['LABEL_BaseExcess', 'LABEL_Fibrinogen', 'LABEL_AST',
                'LABEL_Alkalinephos', 'LABEL_Bilirubin_total', 'LABEL_Lactate',
                'LABEL_TroponinI', 'LABEL_SaO2', 'LABEL_Bilirubin_direct',
                'LABEL_EtCO2']
labels_sepsis = ['LABEL_Sepsis']
labels_VS_mean = ['LABEL_RRate', 'LABEL_ABPm', 'LABEL_SpO2', 'LABEL_Heartrate']
all_labels = labels_tests + labels_sepsis + labels_VS_mean

# Drop pid feature:
train_features = train_features.drop(labels="pid", axis=1)
test_features = test_features.drop(labels="pid", axis=1)
# ---------------------------------------------------------
# ----------------- SET PARAMETERS ------------------------
# ---------------------------------------------------------
features_selection = True

# ---------------------------------------------------------
# ----------------- DATA SELECTION ------------------------
# ---------------------------------------------------------

rd_permutation = np.random.permutation(train_features.index)
train_features = train_features.reindex(rd_permutation).set_index(np.arange(0,train_features.shape[0],1))
train_labels = train_labels.reindex(rd_permutation).set_index(np.arange(0,train_labels.shape[0],1))

# Definition of test and val data size:
# task 1
#train_features.reindex(np.random.permutation(train_features.index))
train_size = 15000
select_houred_features_t1 = houred_features
X_t1 = np.array(train_features.loc[0:train_size - 1, select_houred_features_t1])
X_val_t1 = np.array(train_features.loc[train_size:, select_houred_features_t1])
X_test_t1 = np.array(test_features[select_houred_features_t1])

# task3
# select_features_t3 = ['LABEL_RRate', 'LABEL_ABPm', 'LABEL_SpO2', 'LABEL_Heartrate']
# select_features_t3 = ['Heartrate']
select_features_t3 = all_features
select_houred_features_t3 = sum([[houred_feature + str(i) for i in range(13 - N_hours, 13)]
                                 for houred_feature in select_features_t3], [])
select_houred_features_t3 = houred_features
X_t3 = np.array(train_features.loc[0:train_size - 1, select_houred_features_t3])
X_val_t3 = np.array(train_features.loc[train_size:, select_houred_features_t3])
X_test_t3 = np.array(test_features[select_houred_features_t3])

# Standardize the data
X_t1 = (X_t1 - np.mean(X_t1, 0)) / np.std(X_t1, 0)
X_val_t1 = (X_val_t1 - np.mean(X_val_t1, 0)) / np.std(X_val_t1, 0)
X_test_t1 = (X_test_t1 - np.mean(X_test_t1, 0)) / np.std(X_test_t1, 0)

# Standardize the data
X_t3 = (X_t3 - np.mean(X_t3, 0)) / np.std(X_t3, 0)
X_val_t3 = (X_val_t3 - np.mean(X_val_t3, 0)) / np.std(X_val_t3, 0)
X_test_t3 = (X_test_t3 - np.mean(X_test_t3, 0)) / np.std(X_test_t3, 0)

# these dataframe will contain every prediction
Y_test_tot = pd.DataFrame(np.zeros([X_test_t3.shape[0], len(all_labels)]),
                          columns=all_labels)  # predictions for test set
Y_val_tot = pd.DataFrame(np.zeros([X_val_t3.shape[0], len(all_labels)]), columns=all_labels)  # predictions for val set

# --------------------------------------------------------
# ------------------- TRAINING TASK 1 --------------------
# ---------------------------------------------------------

labels_target = labels_tests + ['LABEL_Sepsis']
# labels_target = ['LABEL_BaseExcess','LABEL_EtCO2','LABEL_SaO2']
# labels_target = ['LABEL_BaseExcess', 'LABEL_EtCO2']
# labels_target = ['LABEL_SaO2']
# labels_target = ['LABEL_Sepsis']
scores_t1 = []
usefulness_matrix = pd.DataFrame(index=select_houred_features_t1, columns=labels_target)

for i in range(0, len(labels_target)):
    label_target = labels_target[i]
    Y_t1 = train_labels[label_target].iloc[0:train_size]
    Y_val_t1 = train_labels[label_target].iloc[train_size:]

    # # find class_weights
    # weight0 = (Y_t1.shape[0] + Y_val_t1.shape[0]) / (sum(Y_t1 != 0) + sum(Y_val_t1 != 0) + 1)
    # weight1 = (Y_t1.shape[0] + Y_val_t1.shape[0]) / (sum(Y_t1 == 0) + sum(Y_val_t1 == 0) + 1)
    # class_weights = {0: weight0, 1: weight1}

    # read the classifics for usefulness

    # feature_classific = np.array(stored_usefulness_matrix[label_target])
    # keep_rate = 0.6
    # N_useful_features = int(keep_rate * np.max(feature_classific))
    # useful_features_mask = feature_classific <= N_useful_features
    if features_selection:
        useful_features_mask = np.array(stored_usefulness_matrix_t1[label_target])
        long_useful_features_mask = np.insert(np.repeat(useful_features_mask[1:],12), 0, useful_features_mask[0])
        X_t1_useful = X_t1[:, long_useful_features_mask]
        X_val_t1_useful = X_val_t1[:, long_useful_features_mask]
        X_test_t1_useful = X_test_t1[:, long_useful_features_mask]
    else:
        X_t1_useful = X_t1
        X_val_t1_useful = X_val_t1
        X_test_t1_useful = X_test_t1

    # fit
    clf = svm.LinearSVC(C=10e-4, class_weight='balanced', tol=10e-3, verbose=0)
    #clf = svm.SVC(C=10e-4, class_weight='balanced', tol=10e-3, verbose=0, kernel='rbf')
    clf.fit(X_t1_useful, Y_t1)

    # # feature selection
    # selector = RFE(clf, 1, step=1, verbose=1)
    # selector = selector.fit(X_t1, Y_t1)
    # usefulness_matrix[label_target] = selector.ranking_

    # predict and save into dataframe
    Y_temp = np.array([clf.decision_function(X_val_t1_useful)])
    Y_val_pred = (1 / (1 + np.exp(-Y_temp))).flatten()
    Y_temp = np.array([clf.decision_function(X_test_t1_useful)])
    Y_test_pred = (1 / (1 + np.exp(-Y_temp))).flatten()
    Y_val_tot.loc[:, label_target] = Y_val_pred
    Y_test_tot.loc[:, label_target] = Y_test_pred

    score = np.mean([skmetrics.roc_auc_score(Y_val_t1, Y_val_pred)])
    scores_t1 = scores_t1 + [score]
    print("ROC AUC -- score ", i, " ", label_target, " :", score)

task1 = sum(scores_t1[:-1]) / len(scores_t1[:-1])
print("ROC AUC task1 score  ", task1)
task2 = scores_t1[-1]
print("ROC AUC task2 score ", task2)


#usefulness_matrix.to_csv('../data/usefulness_matrix.csv', header=True, index=True, float_format='%.7f')

# ---------------------------------------------------------
# ------------------- TRAINING TASK 3 --------------------
# ---------------------------------------------------------

labels_target = labels_VS_mean
# labels_target = ['LABEL_' + select_feature for select_feature in select_features]
scores_t3 = []
for i in range(0, len(labels_target)):
    # get the set corresponding tu the feature
    label_target = labels_target[i]
    Y_t3 = train_labels[label_target].iloc[0:train_size]
    Y_val_t3 = train_labels[label_target].iloc[train_size:]

    if features_selection:
        useful_features_mask = np.array(stored_usefulness_matrix_t3[label_target])
        long_useful_features_mask = np.insert(np.repeat(useful_features_mask[1:],12), 0, useful_features_mask[0])
        X_t3_useful = X_t3[:, long_useful_features_mask]
        X_val_t3_useful = X_val_t3[:, long_useful_features_mask]
        X_test_t3_useful = X_test_t3[:, long_useful_features_mask]
    else:
        X_t3_useful = X_t3
        X_val_t3_useful = X_val_t3
        X_test_t3_useful = X_test_t3

    # fit
    reg = LinearRegression()
    reg.fit(X_t3_useful, Y_t3)
    # reg = Lasso(alpha=2e-1)
    # reg.fit(X_t3_useful, np.ravel(Y_t3))

    # predict and save into dataframe
    Y_test_pred = reg.predict(X_test_t3_useful).flatten()
    Y_val_pred = reg.predict(X_val_t3_useful).flatten()
    Y_test_tot.loc[:, label_target] = Y_test_pred
    Y_val_tot.loc[:, label_target] = Y_val_pred

    score
    score = 0.5 + 0.5 * skmetrics.r2_score(Y_val_t3, Y_val_pred, sample_weight=None, multioutput='uniform_average')
    scores_t3 = scores_t3 + [score]
    print("R2 score ", i, " ", label_target, " :", score)

task3 = np.mean(scores_t3)
print("Task3 score = ", task3)
print("Total score = ", np.mean([task1, task2, task3]))


# save into file
Y_val_tot.insert(0, 'pid', sample['pid'])
Y_test_tot.insert(0, 'pid', sample['pid'])
Y_val_tot.to_csv('../data/predictions.csv', header=True, index=False, float_format='%.7f')
Y_test_tot.to_csv('../data/submission.csv', header=True, index=False, float_format='%.7f')
Y_test_tot.to_csv('../data/submission.zip', header=True, index=False, float_format='%.7f', compression='zip')

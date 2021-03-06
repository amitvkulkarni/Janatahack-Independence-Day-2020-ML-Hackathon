import os
import csv
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import accuracy_score
from fastai.text import *

df_train = pd.read_csv('/content/drive/My Drive/JanataHack_IndependenceDay_MultiLabel/train.csv')
df_test = pd.read_csv('/content/drive/My Drive/JanataHack_IndependenceDay_MultiLabel/test.csv')
df_sub = pd.read_csv('/content/drive/My Drive/JanataHack_IndependenceDay_MultiLabel/sample_submission.csv')

df_train['CONTEXT'] = df_train['TITLE'] + df_train['ABSTRACT']
df_test['CONTEXT'] = df_test['TITLE'] + df_test['ABSTRACT']

df_train.drop(labels = ['TITLE','ABSTRACT'], axis= 1, inplace=True)
df_test.drop(labels = ['TITLE','ABSTRACT'], axis= 1, inplace=True)

###################################################################################################################

df_train['CONTEXT'] = df_train['CONTEXT'].str.replace('([“”¨«»®´·º½¾¿¡§£₤‘’])', '')
df_test['CONTEXT'] = df_test['CONTEXT'].str.replace('([“”¨«»®´·º½¾¿¡§£₤‘’])', '')

data = (TextList.from_df(df_train, cols='CONTEXT')
                .split_by_rand_pct(0.2)
                .label_for_lm()  
                .databunch(bs=48))
data.show_batch()

learn = language_model_learner(data,AWD_LSTM, drop_mult=0.3)

# select the appropriate learning rate
learn.lr_find()

# we typically find the point where the slope is steepest
learn.recorder.plot(suggestion=True)

min_grad_lr = learn.recorder.min_grad_lr
min_grad_lr

# Fit the model based on selected learning rate
learn.fit_one_cycle(5, min_grad_lr, moms=(0.8,0.7))

# Save the encoder for use in classification
learn.save_encoder('fine_tuned_enc')

label_cols = ['Computer Science', 'Physics', 'Mathematics', 'Statistics', 'Quantitative Biology', 'Quantitative Finance']

test_datalist = TextList.from_df(df_test, cols='CONTEXT', vocab=data.vocab)

data_clas = (TextList.from_df(df_train, cols='CONTEXT', vocab=data.vocab)
             .split_by_rand_pct(0.2)
             .label_from_df(cols= label_cols , classes=label_cols)
             .add_test(test_datalist)
             .databunch(bs=128))

data_clas.show_batch()

learn_classifier = text_classifier_learner(data_clas, AWD_LSTM, drop_mult=0.5)

# load the encoder saved  
learn_classifier.load_encoder('fine_tuned_enc')
learn_classifier.freeze()

# select the appropriate learning rate
learn_classifier.lr_find()

# we typically find the point where the slope is steepest
learn_classifier.recorder.plot(suggestion=True)

min_grad_lr2 = learn_classifier.recorder.min_grad_lr
min_grad_lr2

# Fit the model based on selected learning rate
learn_classifier.fit_one_cycle(5, min_grad_lr2, moms=(0.8,0.7))

learn_classifier.show_results()

learn_classifier.freeze_to(-2)
learn_classifier.fit_one_cycle(5, slice(min_grad_lr2/(2.6**4),min_grad_lr2), moms=(0.8,0.7))

learn_classifier.freeze_to(-3)
learn_classifier.fit_one_cycle(5, slice(min_grad_lr2/(2.6**4),min_grad_lr2), moms=(0.8,0.7))

learn_classifier.show_results()

preds, target = learn_classifier.get_preds(DatasetType.Test, ordered=True)
labels = preds.numpy()

labels

df_sub1 = df_sub[['ID']]

submission = pd.concat([df_sub1, pd.DataFrame(preds.numpy(), columns = label_cols)], axis=1)

#submission.to_csv('submission.csv', index=False)
submission.head(200)

submission['Computer Science'] = submission['Computer Science'].apply(lambda x: 1 if x > 0.5 else 0)
submission['Physics'] = submission['Physics'].apply(lambda x: 1 if x > 0.5 else 0)
submission['Mathematics'] = submission['Mathematics'].apply(lambda x: 1 if x > 0.5 else 0)
submission['Statistics'] = submission['Statistics'].apply(lambda x: 1 if x > 0.5 else 0)
submission['Quantitative Biology'] = submission['Quantitative Biology'].apply(lambda x: 1 if x > 0.5 else 0)
submission['Quantitative Finance'] = submission['Quantitative Finance'].apply(lambda x: 1 if x > 0.5 else 0)

submission.head(300)

submission.to_csv("/content/drive/My Drive/JanataHack_IndependenceDay_MultiLabel/submission_fastai9.csv", header=True, index = False)

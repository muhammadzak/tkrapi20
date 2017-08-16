"""
flaskr.py

Demo:
. env.bash
$PYTHON flaskr.py
Other shell:
curl localhost:5011/demo11.json
curl localhost:5011/static/hello.json
"""

import io
import pdb
import os
import flask
import datetime      as dt
import flask_restful as fr
import numpy         as np
import pandas        as pd
import sqlalchemy    as sql
import sklearn.linear_model as skl

# I should connect to the DB
db_s = os.environ['PGURL']
conn = sql.create_engine(db_s).connect()

application = flask.Flask(__name__)
api         = fr.Api(application)

with open('years.txt') as fh:
  years_l = fh.read().split()
  
with open('tkrlist.txt') as fh:
  tkrlist_l = fh.read().split()
  
class Demo11(fr.Resource):
  """
  This class should be a simple syntax demo.
  """
  def get(self):
    my_k_s = 'hello'
    my_v_s = 'world'
    return {my_k_s: my_v_s}
api.add_resource(Demo11, '/demo11.json')

class Tkrlist(fr.Resource):
  """
  This class should list all the tkrs in tkrlist.txt
  """
  def get(self):
    return {'tkrlist': tkrlist_l}
api.add_resource(Tkrlist, '/tkrlist')

class Istkr(fr.Resource):
  """
  This class should answer True, False given a tkr.
  """
  def get(self, tkr):
    torf = tkr in tkrlist_l
    return {'istkr': torf}
api.add_resource(Istkr, '/istkr/<tkr>')

class Years(fr.Resource):
  """
  This class should list all the years in years.txt
  """
  def get(self):
    return {'years': years_l}
api.add_resource(Years, '/years')

class Tkrprices(fr.Resource):
  """
  This class should list prices for a tkr.
  """
  def get(self, tkr):
    # I should get csvh from tkrprices in db:
    sql_s       = '''select csvh from tkrprices
      where tkr = %s  LIMIT 1'''
    result      = conn.execute(sql_s,[tkr])
    if not result.rowcount:
      return {'no': 'data found'}  
    myrow       = [row for row in result][0]
    return {'tkrprices': myrow.csvh.split()}
api.add_resource(Tkrprices, '/tkrprices/<tkr>')

def getfeat(tkr):
  """This function should return a DataFrame full of features for a tkr."""
  sql_s  = "SELECT csv FROM features WHERE tkr = %s LIMIT 1"
  result = conn.execute(sql_s,[tkr])
  if not result.rowcount:
    return {'no': 'data found'}
  myrow  = [row for row in result][0]
  feat_df = pd.read_csv(io.StringIO(myrow.csv))
  feat_df.head()
  return feat_df

#   /sklinear/IBM/25/2016-11?features='pctlag1,slope4,moy'

def get_train_test(tkr,yrs,mnth,features):
  # I should get features for this tkr from db:
  feat_df = getfeat(tkr)
  # I should get the test data from feat_df:
  test_bool_sr = (feat_df.cdate.str[:7] == mnth)
  test_df      =  feat_df.loc[test_bool_sr] # should be about 21 rows
  # I should get the training data from feat_df:
  max_train_loc_i = -1 + test_df.index[0]
  min_train_loc_i = max_train_loc_i - yrs * 252
  if (min_train_loc_i < 10):
    min_train_loc_i = 10
  train_df = feat_df.loc[min_train_loc_i:max_train_loc_i]
  # I should train:
  features_l = features.split(',')
  xtrain_df  = train_df[features_l]
  xtrain_a   = np.array(xtrain_df)
  ytrain_a   = np.array(train_df)[:,2 ]
  xtest_df   = test_df[features_l]
  xtest_a    = np.array(xtest_df)
  out_df     = test_df.copy()[['cdate','cp','pct_lead']]
  return xtrain_a, ytrain_a, xtest_a, out_df

def learn_predict_sklinear(tkr='ABC',yrs=20,mnth='2016-11', features='pct_lag1,slope4,moy'):
  linr_model = skl.LinearRegression()
  pdb.set_trace()
  xtrain_a, ytrain_a, xtest_a, out_df = get_train_test(tkr,yrs,mnth,features)
  # I should get features for this tkr from db:
  feat_df = getfeat(tkr)
  # I should get the test data from feat_df:
  test_bool_sr = (feat_df.cdate.str[:7] == mnth)
  test_df      =  feat_df.loc[test_bool_sr] # should be about 21 rows
  # I should get the training data from feat_df:
  max_train_loc_i = -1 + test_df.index[0]
  min_train_loc_i = max_train_loc_i - yrs * 252
  if (min_train_loc_i < 10):
    min_train_loc_i = 10
  train_df = feat_df.loc[min_train_loc_i:max_train_loc_i]

  features_l = features.split(',')
  xtrain_df  = train_df[features_l]
  xtrain_a   = np.array(xtrain_df)
  ytrain_a   = np.array(train_df)[:,2 ]

  xtest_df = test_df[features_l]
  xtest_a  = np.array(xtest_df)
  out_df   = test_df.copy()[['cdate','cp','pct_lead']]
  
  linr_model.fit(xtrain_a,ytrain_a)
  out_df['prediction']    = np.round(linr_model.predict(xtest_a),3).tolist()
  out_df['effectiveness'] = np.sign(out_df.pct_lead*out_df.prediction)*np.abs(out_df.pct_lead)
  out_df['accuracy']      = (1+np.sign(out_df.effectiveness))/2
  pdb.set_trace()
  return out_df
  
class Sklinear(fr.Resource):
  """
  This class should build an sklearn linear regression model.
  """
  def get(self, tkr,yrs,mnth):
    # I should get features for this tkr from db:
    feat_df = getfeat(tkr)
    # I should get the test data from feat_df:
    test_bool_sr = (feat_df.cdate.str[:7] == mnth)
    test_df      =  feat_df.loc[test_bool_sr] # should be about 21 rows
    # I should get the training data from feat_df:
    max_train_loc_i = -1 + test_df.index[0]
    min_train_loc_i = max_train_loc_i - yrs * 252
    if (min_train_loc_i < 10):
      min_train_loc_i = 10
    train_df = feat_df.loc[min_train_loc_i:max_train_loc_i]
    train_df.head()
    train_df.tail()
    # I should train:
    linr_model = skl.LinearRegression()
    xtrain_a   = np.array(train_df)[:,3:]
    ytrain_a   = np.array(train_df)[:,2 ]
    linr_model.fit(xtrain_a,ytrain_a)
    # I should predict:
    xtest_a = np.array(test_df)[:,3:]
    out_df  = test_df.copy()[['cdate','cp','pct_lead']]
    out_df['prediction'] = linr_model.predict(xtest_a).tolist()
    out_df['effectiveness'] = np.sign(out_df.pct_lead*out_df.prediction)*np.abs(out_df.pct_lead)
    out_df['accuracy'] = (1+np.sign(out_df.effectiveness))/2
    return {'notdone-yet': True}
api.add_resource(Sklinear, '/sklinear/<tkr>/<int:yrs>/<mnth>')
  
if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  application.run(host='0.0.0.0', port=port)
'bye'

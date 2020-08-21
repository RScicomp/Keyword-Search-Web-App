import base64
import datetime
import io


import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output, State

import plotly.express as px
import pandas as pd

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options
global dataset
dataset=None
global allmatches
allmatches=None

global keywordmatchesvals
keywordmatchesvals={}
global combinations
combinations={}



app.layout = html.Div(children=[
    
    html.H1("Filtering System", style={'text-align': 'center'}),
    html.Div(
        [
            dcc.Dropdown(
                id="col-dropdown",
                multi=True,
                value=0,
                options=[
                    {'label': '', 'value': 0}],
            ),
        ],
    ),
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        # Allow multiple files to be uploaded
        multiple=True
    ),
    html.Div([
        html.Center(html.A("download excel", href="/download_excel/")),
    ]),
    html.Div([
        html.Center(dcc.Markdown("""
              **Keywords**
          """)),
        html.Center(dcc.Input(id="keywordmatchvals", type="text", placeholder="")),
        html.Center(dcc.Markdown("""
              **Combinations**
          """)),
        html.Center(dcc.Input(id="combinations", type="text", placeholder="")),

        ],style={
            'borderBottom': 'thin lightgrey solid',
            'backgroundColor': 'rgb(250, 250, 250)',
            'padding': '10px 5px'}
    ),
    html.Hr(),
    html.Center(html.Button('Submit', id='submit-val')),
    html.Hr(),
    html.Center(html.Pre(id='keywordlist')),
    html.Div(id='output-data-upload'),
    html.Center(html.Pre(id='selected')),
])

def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
        global dataset
        dataset=df
        
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])

    return html.Div([
        #html.H5(filename),
        #html.H6(datetime.datetime.fromtimestamp(date)),
        html.Center(dcc.Markdown("**All Data**")),
        dash_table.DataTable(
            data=df.iloc[0:5].to_dict('records'),
            columns=[{'name': i, 'id': i} for i in df.columns],
            style_table={
                'overflowY': 'scroll'
            },
        ),

        html.Hr(),  # horizontal line

        # For debugging, display the raw contents provided by the web browser
        #html.Div('Raw Content'),
        #html.Pre(contents[0:200] + '...', style={
        #    'whiteSpace': 'pre-wrap',
        #    'wordBreak': 'break-all'
        #})
    ])

@app.callback(Output('output-data-upload', 'children'),
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename'),
               State('upload-data', 'last_modified')])
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        return(children)
        #return children


@app.callback(Output('col-dropdown', 'options'),
              [Input('output-data-upload', 'children')])
def update_dropdown(data):
    
    global dataset
    if(data):
        allcols= list(dataset.columns)
        return([{'label': str(allcols[i]), 'value': i} for i in range(0,len(allcols))])
    else:
        return([{'label': '', 'value': 0}])
    
@app.callback(Output('selected', 'children'),
              [Input('col-dropdown', 'value')])
def combine_data(options):
    global dataset
    print(options)
 
    labels=[]
    if(options):
        dataset['Solution'] = ''
        columns=list(dataset.columns)
        if(type(options) == int):
            dataset['Solution'] += " "+dataset[columns[options]]
        for col in options:
            dataset['Solution'] += " "+dataset[columns[col]]
            labels.append(columns[col])
        print(labels)
        #dataset['Solution'] = ''
        #for 
        return html.Div([
            html.Center(dcc.Markdown("**Selected Data**")),
            dash_table.DataTable(
                data=dataset[labels+['Solution']].to_dict('records'),
                columns=[{'name': i, 'id': i} for i in dataset[labels+['Solution']].columns],
                style_table={'overflowY': 'scroll'},
                style_cell={'maxWidth':'180px'},
            ),
            html.Hr(),  # horizontal line
            # For debugging, display the raw contents provided by the web browser
        ])
    
    return(str(labels))
import re
@app.callback(Output('keywordlist', 'children'),
              [Input('keywordmatchvals', 'value'),
              Input('combinations','value'),
              Input("submit-val","n_clicks")])
def keyword_populate(keywordmatch,combos,submit):

    ctx = dash.callback_context
    #print(dataset['Solution'])
    
    if ctx.triggered and submit:
        global keywordmatchesvals
        global combinations
        print("Keywords: " + str(keywordmatchesvals))
        print("Combinations: " + str(combinations))
        keywordmatchesvals={}
        combinations={}

        try:
            for keyword in keywordmatch.split(","):
                word=keyword.split(":")[0].strip()
                value=int(keyword.split(":")[1])
                keywordmatchesvals[word]=value
        except:
            pass
        try:
            allcombos=re.findall('\(([^)]+)', str(combos))

            for combo in allcombos:
                word=combo.split(":")[0].strip()
                values=combo.split(":{")[1].replace("}","").split(",")
                values= {val.split(":")[0].strip():int(val.split(":")[1]) for val in values}
                combinations[word]=values
            print(combinations)
        except:
            pass
        if(isinstance(dataset, pd.DataFrame)):
            print("yes")
            if('Solution' in dataset.columns):
                global allmatches
                allmatches=matchdesj(dataset,list(dataset.columns)[0])
    return(str(keywordmatchesvals) + " " +str(combinations))

def matchdesj(dff,idcol):
    keywordstore=[]
    

    for x,name in zip(dff['Solution'],dff[idcol]):
        if(str(x) != 'nan'):
            x=x.lower()
            words=x.split()
            matches=[]
            combomatches=[]
            productmatches=[]
            sentencews=[]
            sentencep=[]
            score=0
            index=0

            for word in words:
            #print(word)
                global keywordmatchesvals
                global combinations
                for keyword in keywordmatchesvals.keys():
                    lenkey=len(keyword.split(" "))
                    word2=" ".join(words[index:index+lenkey])
                    if(keyword.lower() in word2.lower()):
                        matches.append(keyword)
                        score+=keywordmatchesvals[keyword]
                        sentencews.append(" ".join(words[index-10:index+10]))
                        print(keyword)

                if word in combinations.keys():
                    for compl in combinations[word].keys():
                        if compl in x:
                            #score+=20
                            combomatches.append((word,compl))
                            score+=combinations[word][compl]
                            #productmatches.append(word,compl)
                            sentencews.append(" ".join(words[index-10:index+10]))
            index=index+1


            keywordstore.append((name,productmatches,matches,combomatches,sentencews,x,score))

    return(keywordstore)

import io
import xlsxwriter
from flask import send_file
@app.server.route('/download_excel/')
def download_excel():
    global allmatches
    print(allmatches)
    df = pd.DataFrame(allmatches)
    print(df)
    #Convert DF
    strIO = io.BytesIO()
    excel_writer = pd.ExcelWriter(strIO, engine="xlsxwriter")
    df.to_excel(excel_writer, sheet_name="sheet1")
    excel_writer.save()
    excel_data = strIO.getvalue()
    strIO.seek(0)
    print(excel_data)
    print(strIO.seek(0))
    print(strIO)
    df.to_excel("matches (10).xlsx")
    return send_file(strIO,
                     attachment_filename="matches (10).xlsx",
                     as_attachment=True,
                     cache_timeout=0)

if __name__ == '__main__':
    app.run_server(debug=True)
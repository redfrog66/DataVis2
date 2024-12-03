from flask import Flask, jsonify, render_template, request
import pandas as pd
import plotly
import plotly.express as px
import json

# Flask alkalmazás
app = Flask(__name__, template_folder='templates', static_folder='static')

# CSV fájl beolvasása
df = pd.read_csv('data/Titanic-Dataset.csv')

# - - - HOME PAGE - - -
@app.route('/')
def home():
    # Túlélők és elhunytak számának kiszámítása
    survived_count = df['Survived'].sum()
    died_count = len(df) - survived_count

    # Adatok előkészítése Plotly pie chart-hoz
    data = {'Státusz': ['Túlélők', 'Elhunytak'], 
            'Fő': [survived_count, died_count]}
    fig = px.pie(data, values='Fő', names='Státusz',
                 color='Státusz',
                 color_discrete_map={'Túlélők': 'blue', 'Elhunytak': 'red'},
                 title='Túlélők és Elhunytak Aránya')

    # Szeletek távolsága (explode effect)
    fig.update_traces(marker=dict(line=dict(color='black', width=0.5)),
                      pull=[0.1, 0.1])  # Távollét (pull effect)

    # Diagram JSON formátumban
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return render_template('index.html', graphJSON=graphJSON)

# - - - ÁBRÁK PAGE - - -
def factor_name(factor):
    factor_map = {
        "Sex": "Nem",
        "Age": "Kor",
        "Pclass": "Osztály",
        "Embarked": "Beszállási Hely",
        "SibSp": "Testvérek és Házastársak száma",
        "Parch": "Szülők és Gyerekek száma"
    }
    return factor_map.get(factor, factor)

# Chart1 - Bar Chart
@app.route('/chart1')
def chart1():
    factor = 'Sex'
    grouped = df.groupby([factor, 'Survived']).size().reset_index(name='Count')

    bar_fig = px.bar(
        grouped, x=factor, y='Count', color='Survived',
        barmode='group',
        labels={'Survived': 'Túlélés'},
        title=f"Túlélési arány {factor_name(factor)} szerint"
    )

    bar_json = json.dumps(bar_fig, cls=plotly.utils.PlotlyJSONEncoder)
    return render_template('chart1.html', graphJSON=bar_json)

@app.route('/update_chart1')
def update_chart1():
    factor = request.args.get('factor', 'Sex')
    grouped = df.groupby([factor, 'Survived']).size().reset_index(name='Count')

    bar_fig = px.bar(
        grouped, x=factor, y='Count', color='Survived',
        barmode='group',
        labels={'Survived': 'Túlélés'},
        title=f"Túlélési arány {factor_name(factor)} szerint"
    )

    response = {'bar_chart': json.dumps(bar_fig, cls=plotly.utils.PlotlyJSONEncoder)}
    return jsonify(response)


@app.route('/statistics')
def statistics():
    return render_template('statistics.html')

if __name__ == '__main__':
    app.run(debug=True)
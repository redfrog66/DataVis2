from flask import Flask, render_template, request
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

@app.route('/chart/<int:chart_id>')
def chart(chart_id):
    return render_template('chart1.html')

@app.route('/statistics')
def statistics():
    return render_template('statistics.html')

if __name__ == '__main__':
    app.run(debug=True)
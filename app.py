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

def format_age(age):
    if age >= 1:
        return f"{int(age)} éves"
    else:
        months = round(age * 12)
        return f"{months} hónapos"
    
def get_port_name(code):
    port_names = {
        'C': 'Cherbourg',
        'Q': 'Queenstown',
        'S': 'Southampton'
    }
    return port_names.get(code, 'Ismeretlen kikötő')


@app.route('/statistics')
def statistics():
    # Legidősebb utas
    oldest_passenger = df.loc[df['Age'].idxmax()]
    youngest_passenger = df.loc[df['Age'].idxmin()]
    
    # Kikötő statisztika
    most_common_embarked = df['Embarked'].value_counts().idxmax()
    embarked_count = df['Embarked'].value_counts().max()
    most_common_embarked_name = get_port_name(most_common_embarked)  # Kikötő nevének meghatározása
    
    # Osztály statisztika
    most_common_class = df['Pclass'].value_counts().idxmax()
    class_count = df['Pclass'].value_counts().max()
    
    # Legdrágább jegy
    most_expensive_ticket = df.loc[df['Fare'].idxmax()]
    
    # Adatok formázása
    statistics = {
        'oldest_passenger': {
            'name': oldest_passenger['Name'],
            'age': format_age(oldest_passenger['Age']),
        },
        'youngest_passenger': {
            'name': youngest_passenger['Name'],
            'age': format_age(youngest_passenger['Age']),
        },
        'most_common_embarked': {
            'port': most_common_embarked_name,
            'count': embarked_count,
        },
        'most_common_class': {
            'class': most_common_class,
            'count': class_count,
        },
        'most_expensive_ticket': {
            'name': most_expensive_ticket['Name'],
            'fare': f"{most_expensive_ticket['Fare']:.2f}",
            'class': most_expensive_ticket['Pclass'],
        }
    }

    return render_template('statistics.html', statistics=statistics)



if __name__ == '__main__':
    app.run(debug=True)
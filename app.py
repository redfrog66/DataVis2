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

@app.route('/tree1')
def tree1():
    # ---- Treemap 1: Túlélési arány nem és jegytípus szerint ----
    # Alapértelmezett tényezők és csoportosítás
    grouped = df.groupby(['Survived', 'Sex', 'Pclass']).size().reset_index(name='Count')

    # 'Survived' értékek lecserélése érthetőbb kifejezésekre
    grouped['Survived'] = grouped['Survived'].replace({
        0: 'Elhunyt', 
        1: 'Túlélt'
    })

    # 'Sex' értékek lecserélése magyar kifejezésekre
    grouped['Sex'] = grouped['Sex'].replace({
        'male': 'Férfi',
        'female': 'Nő'
    })

    # Treemap létrehozása
    tree_fig = px.treemap(
        grouped,
        path=['Survived', 'Sex', 'Pclass'],  # Hierarchikus bontás
        values='Count',  # Téglalap méretét befolyásoló adat
        color='Count',  # Színezés a Count értékek alapján
        color_continuous_scale='Blues',  # Színskála
        title="Titanic túlélési arány hierarchikus bontásban túlélés, nem és jegytípus alapján"
    )

    # Hover szöveg formázása
    tree_fig.update_traces(
        hovertemplate=(
            '<b>Státusz:</b> %{label}<br>' +
            '<b>Nem:</b> %{parent}<br>' +
            '<b>Utasok száma:</b> %{value}<extra></extra>'
        )
    )

    # JSON konvertálás
    tree_json = json.dumps(tree_fig, cls=plotly.utils.PlotlyJSONEncoder)

# ---- Treemap 2: Teljes utaslista hierarchikus bontásban ----
    df['Age'] = df['Age'].fillna(-1)  # Ha van NaN, akkor -1-el pótoljuk
    df['AgeCategory'] = pd.cut(
        df['Age'], 
        bins=[-1, 10, 25, 40, 50, 120],  # -1 biztosítja, hogy a 0 alatti korok is megfelelően bekerüljenek
        labels=['<10 éves', '10-25', '25-40', '40-50', '50+'],
        right=False  # Az alsó határ kizárásával biztosítjuk, hogy -1 < 10 a kategóriában legyen
    )


    # A groupby és a treemap létrehozása
    grouped2 = df.groupby(['Survived', 'Embarked', 'Pclass', 'AgeCategory']).size().reset_index(name='Count')
    grouped2['Survived'] = grouped2['Survived'].replace({0: 'Elhunyt', 1: 'Túlélt'})
    grouped2['Embarked'] = grouped2['Embarked'].replace({'C': 'Cherbourg', 'Q': 'Queenstown', 'S': 'Southampton'})
    grouped2 = grouped2[grouped2['Count'] > 0]

    # Treemap létrehozása
    tree2_fig = px.treemap(
        grouped2,
        path=[px.Constant('Összes utas'), 'Survived', 'Embarked', 'Pclass', 'AgeCategory'],
        values='Count',
        color='Count',
        color_continuous_scale='Greens',
        title="Titanic teljes utaslista hierarchikus bontásban"
    )

    tree2_fig.update_traces(
        hovertemplate=(
            '<b>Kategória:</b> %{label}<br>' +
            '<b>Utasok száma:</b> %{value}<extra></extra>'
        )
    )

    tree2_json = json.dumps(tree2_fig, cls=plotly.utils.PlotlyJSONEncoder)


    # Renderelés
    return render_template('tree1.html', treeJSON=tree_json, tree2JSON=tree2_json)

@app.route('/sunburst')
def sunburst():
    # ---- Sunburst 1: Túlélési arány nem és jegytípus szerint ----
    grouped = df.groupby(['Survived', 'Sex', 'Pclass']).size().reset_index(name='Count')

    # 'Survived' értékek lecserélése érthetőbb kifejezésekre
    grouped['Survived'] = grouped['Survived'].replace({
        0: 'Elhunyt', 
        1: 'Túlélt'
    })

    # 'Sex' értékek lecserélése magyar kifejezésekre
    grouped['Sex'] = grouped['Sex'].replace({
        'male': 'Férfi',
        'female': 'Nő'
    })

    # Sunburst diagram létrehozása
    sunburst_fig = px.sunburst(
        grouped,
        path=['Survived', 'Sex', 'Pclass'],  # Hierarchikus bontás
        values='Count',  # Téglalap méretét befolyásoló adat
        color='Count',  # Színezés a Count értékek alapján
        color_continuous_scale='Blues',  # Színskála
        title="Titanic túlélési arány hierarchikus bontásban túlélés, nem és jegytípus alapján"
    )

    # Hover szöveg formázása
    sunburst_fig.update_traces(
        hovertemplate=( 
            '<b>Státusz:</b> %{label}<br>' +
            '<b>Nem:</b> %{parent}<br>' +
            '<b>Utasok száma:</b> %{value}<extra></extra>'
        )
    )

    # JSON konvertálás
    sunburst_json = json.dumps(sunburst_fig, cls=plotly.utils.PlotlyJSONEncoder)

    # ---- Sunburst 2: Teljes utaslista hierarchikus bontásban ----
    df['Age'] = df['Age'].fillna(-1)  # NaN értékek kezelése

    df['AgeCategory'] = pd.cut(
        df['Age'], 
        bins=[-1, 10, 25, 40, 50, 120],  # Kategóriák
        labels=['<10 éves', '10-25', '25-40', '40-50', '50+']
    )

    grouped2 = df.groupby(['Survived', 'Embarked', 'Pclass', 'AgeCategory']).size().reset_index(name='Count')
    grouped2['Survived'] = grouped2['Survived'].replace({0: 'Elhunyt', 1: 'Túlélt'})
    grouped2['Embarked'] = grouped2['Embarked'].replace({'C': 'Cherbourg', 'Q': 'Queenstown', 'S': 'Southampton'})
    grouped2 = grouped2[grouped2['Count'] > 0]

    # Sunburst diagram létrehozása
    sunburst2_fig = px.sunburst(
        grouped2,
        path=[px.Constant('Összes utas'), 'Survived', 'Embarked', 'Pclass', 'AgeCategory'],
        values='Count',
        color='Count',
        color_continuous_scale='Greens',
        title="Titanic teljes utaslista hierarchikus bontásban"
    )

    sunburst2_fig.update_traces(
        hovertemplate=( 
            '<b>Kategória:</b> %{label}<br>' +
            '<b>Utasok száma:</b> %{value}<extra></extra>'
        )
    )

    sunburst2_json = json.dumps(sunburst2_fig, cls=plotly.utils.PlotlyJSONEncoder)

    # Renderelés, átadva a JSON ábrákat
    return render_template('sunburst.html', 
                           sunburst_json=sunburst_json, 
                           sunburst2_json=sunburst2_json)


@app.route('/jegyek')
def jegyek():
    # Csoportosítás az 'Fare' és 'Pclass' oszlopok alapján
    grouped_data = df.groupby(['Fare', 'Pclass']).size().reset_index(name='Eladott jegyek')

    # Megkeressük a legdrágább jegyet
    max_fare = df['Fare'].max()  # A legdrágább jegy ára
    max_fare_tickets = df[df['Fare'] == max_fare]  # Minden jegy, ami a legdrágább
    passengers_info = max_fare_tickets[['Name', 'Survived']]  # Utasok neve és túlélési státusza
    
    # Túlélési státusz hozzáadása
    passengers_info['Survived'] = passengers_info['Survived'].apply(lambda x: 'Túlélte' if x == 1 else 'Nem túlélte')

    # Az összes utas neve és túlélési státusza egy stringbe fűzve
    passenger_details = '<br>'.join([f"{row['Name']}, {row['Survived']}" for index, row in passengers_info.iterrows()])

    # Ábra létrehozása
    fig = px.scatter(
        grouped_data,
        x='Fare',
        y='Eladott jegyek',
        color='Pclass',  # Szín a Pclass szerint
        color_discrete_map={
            '1': 'blue',    # Pclass 1 szín: kék
            '2': 'green',   # Pclass 2 szín: zöld
            '3': 'red'      # Pclass 3 szín: piros
        },
        title="Jegyárak és Eladott Jegyek",
        labels={'Fare': 'Jegy Ár', 'Eladott jegyek': 'Eladott Jegyek'},
        template="plotly_dark"  # Téma (választható)
    )
    
    # A legdrágább jegyhez tartozó utasok és túlélési státusz annotáció
    fig.add_annotation(
        x=max_fare, 
        y=grouped_data[grouped_data['Fare'] == max_fare]['Eladott jegyek'].values[0],
        text=f"Legdrágább jegy:<br>{passenger_details}",
        showarrow=True,
        arrowhead=2,
        ax=0,
        ay=-40,
        font=dict(size=12, color="white"),
        bgcolor="rgba(0, 0, 0, 0.7)",
        align="center"
    )
    
    # Az ábra HTML formátumban történő átadása
    graph_html = fig.to_html(full_html=False)

    # Név előtagok és színek kinyerése
    df['Title'] = df['Name'].apply(lambda x: x.split(',')[1].split('.')[0].strip())
    # Női és férfi előtagok listája

    female_titles = ['Mrs', 'Miss', 'Mme', 'Ms', 'Mlle', 'Lady', 'the Countess']
    male_titles = ['Mr', 'Master', 'Don', 'Rev', 'Major', 'Sir', 'Col', 'Capt', 'Jonkheer']

    def assign_gender_color(title):
        if title in female_titles:
            return 'pink'  # női
        elif title in male_titles:
            return 'blue'  # férfi
        else:
            return 'orange'  # vegyes

    df['GenderColor'] = df['Title'].apply(assign_gender_color)

    # Ábra létrehozása a név előtagok alapján, abc sorrendben
    fig2 = px.scatter(
        df,
        x='Title',
        y='Fare',
        color='GenderColor',
        size='Fare',  # A körök mérete az eladott jegyek számától függhet
        color_discrete_map={
            'pink': 'pink',  # Női előtag: rózsaszín
            'blue': 'blue',  # Férfi előtag: kék
            'orange': 'orange'  # Vegyes nemek aránya: narancssárga
        },
        title="Jegyárak és Eladott Jegyek név-előtagok szerint",
        labels={'Fare': 'Jegy Ár', 'Title': 'Előtag'},
        template="plotly_dark",
        category_orders={
            'Title': sorted(df['Title'].unique())  # Az 'Title' értékek abc sorrendbe rendezése
        }
    )


    # Ábrák HTML formátumban történő átadása
    graph2_html = fig2.to_html(full_html=False)

    # A két ábra egyesítése a sablonban
    return render_template('jegyek.html', graph_html=graph_html, graph2_html=graph2_html)


if __name__ == '__main__':
    app.run(debug=True)
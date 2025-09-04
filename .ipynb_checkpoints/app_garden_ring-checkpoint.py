import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import time
from datetime import timedelta
from scipy.stats import percentileofscore

#load data from csv
data = pd.read_csv('all_runners.csv')
# fill NA with zeros
data.fillna(0, inplace=True)
#keep finishers only
data = data[data['status'] == 'Q']
#remove empty and miscellaneous columns
data = data.drop(columns = ['category', 'status_message', 'status', 'race_name', 'rank_category'])
#add a timedela column for plots' labels (Time column is object type)
data['Time_format'] = pd.to_timedelta(data['result'], errors='coerce')
#add pace
#calculate seconds per km
data['pace_seconds'] = data['result_time'] / (data['result_distance'] / 1000)
#format as mm:ss per km
data["pace_str"] = pd.to_timedelta(data["pace_seconds"], unit="s").dt.components.apply(
    lambda row: f"{int(row['minutes']):02d}:{int(row['seconds']):02d}", axis=1
)

st.title("🏃 Бегуны")

# Distance options
distances = [int(d) for d in sorted(data['result_distance'].unique())]
distance_map = {
    2500: "2.5 км",
    5000: "5 км",
    10000: "10 км",
    16000: "16 км"
}

#add slider
selected_label = st.select_slider(
    "Выберите дистанцию:",
    options=list(distance_map.values()),
    value='16 км'
    )

#make tick marks below
options = list(distance_map.values())
fake_labels = [""] + options[1:-1] + [""]
st.markdown("<div style='display: flex; justify-content: space-between; width: 100%;'>"\
    + "".join([f"<span>{label}</span>" for label in fake_labels])\
    + "</div>",\
    unsafe_allow_html=True
    )
#convert label back to number
selected_distance = [k for k,v in distance_map.items() if v == selected_label][0]

# Filter dataframe by selected distance
df = data[data['result_distance'] == selected_distance]

# Input box for bib number
query = st.text_input("Введите номер или фамилию:", "").strip()

# Histogram of all results
fig = px.histogram(
    df,
    x="result_time",
    title='Распределение бегунов по общему времени',
    nbins=50,
    labels={"result": "Время"},
    color = "gender", color_discrete_map={'female':'salmon', 'male':'cornflowerblue'}, 
    opacity = 0.8, height = 500
)

#print total number of runners
st.write(f"Финишировали {len(df)} бегунов на дистанции {selected_distance/1000} км")
st.write(f"в т.ч. {len(df[df['gender'] == 'male'])} мужчин и {len(df[df['gender'] == 'female'])} женщин")
#calculate median in hours minutes and seconds
seconds = df['result_time'].median()
hours = int(seconds // 3600)
minutes = int((seconds % 3600) // 60)
secs = int(seconds % 60)
st.write('Медианное время: ' + str(hours) +':'+ str(minutes) +':'+ str(secs))

#add median to plot
fig.add_vline(x = seconds, line_color='purple',
             annotation_text='Медианное время: ' + str(hours) +':'+ str(minutes) +':'+ str(secs),
             annotation_position="top")

# добавим границы столбцов
fig.update_traces(marker_line_width = 1, marker_line_color = 'navy')

# Customize ticks to show HH:MM:SS
tick_interval = 300  # every 5 minutes
min_time = int(data['result_time'].min())
max_time = int(data['result_time'].max())

#generate tick values and tick text
t_vals = list(range(min_time, max_time + tick_interval, tick_interval))
t_text = [str(timedelta(seconds=s)) for s in t_vals]

fig.update_layout(xaxis_title='Время', yaxis_title='Кол-во',
    xaxis=dict(
        tickmode='array',
        tickvals=t_vals,
        ticktext=t_text,
        tickangle=45
        )
    )
runner = None
if query:
# If bib entered, add a vertical line for this runner
    if query.isdigit():
        if (df['bib'].astype('str') == str(query)).any():
            match = df[df['bib'].astype('str') == str(query)]
        else:
            st.write(f'Номер {query} не найден')
    else:
        match = df[df['name'].str.contains(query, case=False, na=False)]
    
    if not match.empty:
        if match.shape[0] > 1:
            choice = st.selectbox(
                "Найдено несколько совпадений — выберите бегуна:",
                [f"{row['name']} (№{row['bib']}, {row['result']})" for _, row in match.iterrows()]
            )
            # find the row corresponding to chosen option
            chosen_bib = choice.split("№")[1].split(",")[0]
            runner = match[match['bib'].astype(str) == str(chosen_bib)]
        else:
            runner = match
    else:
        st.write(f'Бегун {query} не найден')
        
    if runner is not None and not runner.empty:
        row = runner.iloc[0]
        fig.add_vline(
            x=row['result_time'],
            line_color="gold",
            line_width=3,
            annotation_text=f"{row['name']} ({row['bib']})<br>{row['result']}",
            annotation_position="top right"
            )
        #add place
        st.write(f'{row['name']}:')
        st.write(f'- на {int(row['rank_abs'])} месте среди всех бегунов')
        #add place by gender
        if row['gender'] == 'female':
            st.write(f'- на {int(row['rank_gender'])} месте среди женщин')
        else:
            st.write(f'- на {int(row['rank_gender'])} месте среди мужчин')
        #add percentile
        val = round(100 - percentileofscore(df['result_time'], row['result_time']), 2)
        st.write(f"- быстрее {val}% бегунов")

st.plotly_chart(fig, use_container_width=True)
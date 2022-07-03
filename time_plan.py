# -*- coding: utf-8 -*-
"""
Created on Fri Jul  1 16:24:04 2022

@author: Vladi
"""

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw 
import os
import pandas as pd
from collections import namedtuple
import datetime
import holidays
from pandas.tseries.offsets import CustomBusinessDay
import streamlit as st

directory = os.getcwd()

font_path = '/System/Library/Fonts/Arial'

def align_text(coordinates):
    return (coordinates[0]+5, coordinates[1]-40)

yellow = (255,255,0)
blue = (0,0,255)
red = (255,0,0)
green = (0,255,0)
magenta = (255,0,255)
cyan = (0,255,255)

font_file = os.path.join(directory, 'arial.ttf')

font = ImageFont.truetype(font_file, 70)
legend_font = ImageFont.truetype(font_file, 35)

bereiche = {
    'T': ((125,551), (1225,533), (1202,916), (177,945)),
    'A': ((125,551), (590,543), (590,640), (123,649)),
    'B': ((758,543), (1225,533), (1225,623), (762,638)),
    'C': ((175,793), (359,790), (362,936), (177,945)),
    'D': ((573,721), (720,720), (723,894), (575,905)),
    'E': ((1016,775), (1196,774), (1202,916), (1014,923)),
    'F': ((1492,508), (1839,440), (1855,530), (1512,597)),
    'G': ((1377,700), (1526,676), (1560,850), (1415,877)),
    'H': ((1707,730), (1857,743), (1840,930), (1691,907)), 
}


# Filling the BW-calender with Holidays and Winter and Sommer pauses

today = datetime.datetime.today()
weekmask_ger = 'Mon Tue Wed Thu Fri'
german_holidays=[date[0] for date in holidays.Germany(years=list(range(2020,2040)),prov='BW').items()]

for year in range(2020,2030):
    # adding the summer pause (CW 33,34) and the winter pause (CW52,CW1)
    for week in [52,1]:
        for day in range(7):
            week1 = f"{year}-W{week}"
            day1 = datetime.datetime.strptime(week1 + '-1', "%Y-W%W-%w")+datetime.timedelta(days=day)
            german_holidays.append(day1)

german_bday = CustomBusinessDay(holidays=german_holidays, weekmask=weekmask_ger)

# Time Plan
houses = 'TABCDEFGH'
floors=[1,3,2,3,3,3,3,3,3]
floors = [i+2 for i in floors]
wall_framework = 2
wall_reinforcement = 2
wall_concrete = 1

slab_framework = 2
slab_reinforcement = 2
slab_concrete = 1

start = datetime.datetime.strptime('2022-03-01','%Y-%m-%d')

house_info = namedtuple('House_info', ['house_number','floor'])
task_info = namedtuple('Task_info',['task_floor_name','duration'])
house_list = [house_info(house, floor) for house, floor in zip(houses, floors)]

floor_tasks_names = [
'slab_framework',
'slab_reinforcement',
'slab_concrete',
'wall_framework',
'wall_reinforcement',
'wall_concrete',
]

floor_tasks_duration = [slab_framework,slab_reinforcement,slab_concrete,wall_framework,wall_reinforcement,wall_concrete]

floor_tasks = [task_info(name, duration) for name, duration in zip(floor_tasks_names, floor_tasks_duration)]

legend = {'Schalung - Decke':[yellow, (30,90,130,140)],   
'Bewehrung - Decke': [blue, (530,90,640,140)],
'Betonierung - Decke': [red, (1030,90, 1130, 140)],
'Schalung - Waende': [green, (30,1110, 130,1160)],
'Bewehrung - Waende': [magenta, (530,1110, 630, 1160)],
'Betonierung - Waende':[cyan, (1030,1110, 1130, 1160)]
}

time_plan = dict()
_id=0

for house in house_list:  
    for floor in range(house.floor):
        for task in floor_tasks:
            if _id==0:
                task_start = start
            elif house.house_number=='F' and floor==0 and task.task_floor_name=='slab_framework':
                task_start = (start+german_bday*5).to_pydatetime()    
            else:
                task_start = (time_plan[_id-1]['end']+german_bday*1).to_pydatetime()
            
            time_plan[_id] = {
                'house_number':house.house_number, 
                'floor':floor+1, 
                'task':task.task_floor_name, 
                'start':task_start,
                'duration':task.duration,
                'end':(task_start+german_bday*(task.duration+1)).to_pydatetime(),
                'before':['' if _id==0 else _id-1],
                }
            _id+=1
    for task in floor_tasks[:3]:
        if house.house_number!='T':
            time_plan[_id] = {
                'house_number':house.house_number, 
                'floor':'Dach', 
                'task':task.task_floor_name, 
                'start':(start if _id==0 else (time_plan[_id-1]['end']+german_bday*1).to_pydatetime()),
                'duration':task.duration,
                'end':((start if _id==0 else time_plan[_id-1]['end'])+german_bday*(task.duration+1)).to_pydatetime(),
                'before':['' if _id==0 else _id-1],
                }
            _id+=1

df=pd.DataFrame(time_plan.values(), columns = time_plan[0].keys(), index = time_plan.keys())

the_date = datetime.datetime.combine(st.date_input('Datum eingeben', today), datetime.datetime.min.time())

img = Image.open(os.path.join(directory,'test_flaechenterminplan.jpg'))

if the_date in german_holidays or the_date.weekday()>=5:
    st.write('Feiertag oder Wochenende ausgewaehlt. Bitta ein anderes Datum eingeben')
    df1 = df.drop(columns=['duration', 'before']).astype(str)
else:
    draw = ImageDraw.Draw(img)
    
    for colour in legend:
        draw.rectangle(xy= legend[colour][1], fill=legend[colour][0], outline=(0,0,0))
        draw.text(align_text(legend[colour][1][2:]), colour, font = legend_font, fill=(0,0,0))
    
    
    for index, row in df[(df.start<=the_date)&(the_date<=df.end)].iterrows():
        bereich = bereiche[row.house_number]
        if  row.task == 'slab_framework':
            the_colour = yellow
        elif row.task == 'slab_reinforcement':
            the_colour = blue
        elif row.task == 'slab_concrete':
            the_colour = red
        elif row.task == 'wall_framework':
            the_colour = green
        elif row.task == 'wall_reinforcement':
            the_colour = magenta
        elif row.task =='wall_concrete':
            the_colour = cyan
        draw.polygon(bereich, fill =the_colour, outline ="black")
        
        draw.text(bereich[0], f'OG {str(row.floor)}', font = font, fill=(0,0,0))
        
    
    draw.text((1600, 1200), str(the_date.strftime('%d.%m.%Y')), font = font, fill=(0,0,0))
    df1 = df[(df.start<=the_date)&(the_date<=df.end)].drop(columns=['duration', 'before']).astype(str)
    
st.image(img)
st.write(df1)



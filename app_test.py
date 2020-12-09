from datetime import datetime
import pandas as pd
import numpy as np

import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output


app = dash.Dash(__name__)

# ------------------------------------------------------------------------------
# Import and clean data
feedback_360 = pd.read_excel('360_feedback.xlsx')
target = pd.read_excel('target.xlsx')
talent = pd.read_excel('talent.xlsx')
job_signatures = pd.read_excel("job_signatures.xlsx")
job_history = pd.read_excel("job_history.xlsx")

def yearsinfunction(hist):
  hist = hist.sort_values(['Unique ID', 'Effective Date']) # sort value by ID and date
  yearsinjob = (hist.groupby('Unique ID')['Effective Date'].shift(-1, fill_value=pd.datetime.today()) \
    - hist.groupby('Unique ID')['Effective Date'].shift(0))/np.timedelta64(1, 'Y') # calculate years in this role
  hist['yearsinjob'] = yearsinjob.round(1)
  yearsinfunction = hist.groupby(['Unique ID','Function'])['yearsinjob'].sum() # calculate years in this function
  hist = hist.merge(yearsinfunction, how = 'left', on=['Unique ID','Function']) \
    .rename(columns={"yearsinjob_x": "yearsinjob", "yearsinjob_y": "yearsinfunction"})
  hist['weighted_yearsinfunction'] = hist['yearsinfunction'] * hist['Pay Scale Group'] # weight the years
  output = hist[['Unique ID', 'Function', 'yearsinfunction', 'weighted_yearsinfunction']].drop_duplicates(subset=['Unique ID', 'Function'], keep='first')
  output = output.rename(columns={'yearsinfunction': 'Time in Function (years)', 'weighted_yearsinfunction': 'Time in Function Weighted (years)'})
  return output

job_history['Function'] = job_history['Function'].replace(['Tax','Accounting'], 'Finance')
job_history['Function'] = job_history['Function'].replace(['Coffee'], 'Culinary')
job_history['Function'] = job_history['Function'].replace(['Facilities'], 'People')
job_history['Function'] = job_history['Function'].replace(['Global Development'], 'Development')
time_in_function = yearsinfunction(job_history)
target['Position Key'] = target['Position'].astype(str) + " " + target['Position Text']

# swap 'communication' and 'working with others'
titles = list(talent.columns)
titles[6], titles[7] = titles[7], titles[6]
talent = talent[titles]

talent_pool = talent.merge(target, how="left", left_on='Unique ID', right_on='Unique ID')
talent_pool = talent_pool.rename(columns={"9box Score (box number 1-9)": "9Box Score"})
talent_pool['Sum of Weighted Differences'] = np.nan
talent_pool['Sum of Weighted Differences (Absolute)'] = np.nan
talent_pool['Time in Function (years)'] = np.nan
talent_pool['Time in Function Weighted (years)'] = np.nan
position_pool = target.merge(job_signatures, left_on="Job Profile", right_on="Job Profile Name")
position_pool = position_pool.rename(columns={"Communication": "Communications"})
position_pool = position_pool.rename(columns={"Influence and Negotiation": "Influence & Negotiation"})
position_pool = position_pool.rename(columns={"Job Family Group_x": "Job Family Group"})
position_pool['Sum of Weighted Differences'] = np.nan
position_pool['Sum of Weighted Differences (Absolute)'] = np.nan

# The following code finds and cuts the wrong scores (those were added twice) in half
wrong_list=[]
for row in range(0, talent_pool.iloc[:, 3:17].shape[0]):
  for col in range(1, talent_pool.iloc[:, 3:17].shape[1]):
    if talent_pool.iloc[:, 3:17].iloc[row, col] == 6:
      if row not in wrong_list:
        wrong_list.append(row)
for row in wrong_list:
  for column in range(3, 18):
    talent_pool.iloc[row, column] = talent_pool.iloc[row, column].astype(int)/2

# ------------------------------------------------------------------------------
# Prepare for app layout
# Fill a position with the right employee
# Choose the position you want to fill
position_list = np.sort(target['Position Key'].unique())
position_option = [{'label': i, 'value': i} for i in position_list]

# Choose the constraints
employee_level_list = np.sort(talent_pool['Employee Level'].unique())
employee_level_option = [{'label': i, 'value': i} for i in employee_level_list]

function_list = np.sort(target['Function'].unique().astype(str))
function_option = [{'label': i, 'value': i} for i in function_list]

location_list = np.sort(target['Location'].unique().astype(str))
location_option = [{'label': i, 'value': i} for i in location_list]

# Find an employee the right position
employee_list = np.sort(talent['Unique ID'].unique())
employee_option = [{'label': i, 'value': i} for i in employee_list]

job_profile_pay_band_list = np.sort(target['Job Profile Pay Band'].unique())
job_profile_pay_band_option = [{'label': i, 'value': i} for i in job_profile_pay_band_list]

# ------------------------------------------------------------------------------
# App layout

app.layout = html.Div([
    dcc.Tabs([
        dcc.Tab(label='Fill A Position With The Right Employee', children=[

        html.H1(children='RBI Succession Planning System', className='six columns'),

        html.Br(),

        html.H4("Please choose the target position:"),
        dcc.Dropdown(id="slct_position",
                     options=position_option,
                     multi=False,
                     searchable=True,
                     placeholder="Target Position"
                     ),

        html.Br(),

        html.H4("Please select time scale:"),
        dcc.Dropdown(id="slct_time_scale_employee",
                     options=[
                        {'label': 'Ready Now', 'value': 'Ready Now'},
                        {'label': 'Ready Soon', 'value': 'Ready Soon'},
                        {'label': 'Ready Later', 'value': 'Ready Later'}
                     ],
                     multi=False,
                     searchable=True,
                     placeholder="Time Scale"
                     ),

        html.Br(),

        html.H4("Please select relevant employee preferences:"),

        dcc.Dropdown(id="slct_employee_level",
                     options=employee_level_option,
                     multi=True,
                     searchable=True,
                     placeholder="Employee Level"
                     ),

        html.Br(),

        dcc.Dropdown(id="slct_employee_function",
                     options=function_option,
                     multi=True,
                     searchable=True,
                     placeholder="Function"
                     ),

        html.Br(),

        dcc.Dropdown(id="slct_employee_location",
                     options=location_option,
                     multi=True,
                     searchable=True,
                     placeholder="Location"
                     ),

        html.Br(),

        dcc.Dropdown(
                id='slct_9box',
                options=[
                    {'label': '1', 'value': 1},
                    {'label': '2', 'value': 2},
                    {'label': '3', 'value': 3},
                    {'label': '4', 'value': 4},
                    {'label': '5', 'value': 5},
                    {'label': '6', 'value': 6},
                    {'label': '7', 'value': 7},
                    {'label': '8', 'value': 8},
                    {'label': '9', 'value': 9}
                ],
                multi=True,
                searchable=True,
                placeholder="9 Box Score"
            ),

        html.Br(),

        dcc.Dropdown(
            id='tip',
            options=[
                {'label': '6', 'value': 6},
                {'label': '12', 'value': 12},
                {'label': '18', 'value': 18},
                {'label': '24', 'value': 24}
            ],
            multi=False,
            searchable=False,
            placeholder="Minimum Time In Position Target (Months)"
        ),

        html.Br(),

        dcc.Dropdown(
            id='til',
            options=[
                {'label': '12', 'value': 12},
                {'label': '18', 'value': 18},
                {'label': '24', 'value': 24},
                {'label': '30', 'value': 30},
                {'label': '36', 'value': 36}
            ],
            multi=False,
            searchable=True,
            placeholder="Minimum Time In Level Target (Months)"
        ),

        html.Br(),
        html.Br(),
        html.Br(),

        dash_table.DataTable(
            id='output1',
            columns=[{"name": i, "id": i} for i in position_pool[['Position', "Position Text", "Manager Unique ID", "Job Profile", "Job Profile Pay Band",
                              "Job Family Group", "Company Code", "Location", "Organization", "Function", "Department", "Specialist / Generalist", "Qualification/Certification?",
                              'Quantitative', 'Analytical', 'Conceptual', 'Communications', 'Working with Others',
                              'Influence & Negotiation', 'Work Management', 'People Management',
                              'Inspiring Leadership', 'Company', 'Industry Knowledge', 'General Business Knowledge',
                              'Functional Expertise', 'Mentoring']].columns],
            data=position_pool[['Position', "Position Text", "Manager Unique ID", "Job Profile", "Job Profile Pay Band",
                              "Job Family Group", "Company Code", "Location", "Organization", "Function", "Department", "Specialist / Generalist", "Qualification/Certification?",
                              'Quantitative', 'Analytical', 'Conceptual', 'Communications', 'Working with Others',
                              'Influence & Negotiation', 'Work Management', 'People Management',
                              'Inspiring Leadership', 'Company', 'Industry Knowledge', 'General Business Knowledge',
                              'Functional Expertise', 'Mentoring']].to_dict('records'),
            export_format="csv",

            style_cell={
                'font_family': 'arial',
                'font_size': '14px',
                'text_align': 'left'
            },

            style_table={'overflowX': 'auto'},

            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(248, 248, 248)'
                }
            ],
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            }
        ),

            html.Br(),
            html.Br(),
            html.Br(),

        dash_table.DataTable(
            id='output2',
            columns=[{"name": i, "id": i} for i in talent_pool[['Unique ID', "Employee Level", "9Box Score", 'Position Text', "Mobility", "Employee Preference", "Location", "Function", "Time in Position (months)", "Time in Level (months)", "Time in Company (years)",
                              'Time in Function (years)', 'Time in Function Weighted (years)', 'Quantitative', 'Analytical', 'Conceptual', 'Communications', 'Working with Others',
                              'Influence & Negotiation', 'Work Management', 'People Management',
                              'Inspiring Leadership', 'Company', 'Industry Knowledge', 'General Business Knowledge',
                              'Functional Expertise', 'Mentoring', 'Sum of Weighted Differences', 'Sum of Weighted Differences (Absolute)']].columns],
            data=talent_pool[['Unique ID', "Employee Level", "9Box Score", 'Position Text', "Mobility", "Employee Preference", "Location", "Function", "Time in Position (months)", "Time in Level (months)", "Time in Company (years)",
                              'Time in Function (years)', 'Time in Function Weighted (years)', 'Quantitative', 'Analytical', 'Conceptual', 'Communications', 'Working with Others',
                              'Influence & Negotiation', 'Work Management', 'People Management',
                              'Inspiring Leadership', 'Company', 'Industry Knowledge', 'General Business Knowledge',
                              'Functional Expertise', 'Mentoring', 'Sum of Weighted Differences', 'Sum of Weighted Differences (Absolute)']].to_dict('records'),
            export_format="csv",

            style_cell={
                'font_family': 'arial',
                'font_size': '14px',
                'text_align': 'left'
            },

            style_table={'overflowX': 'auto'},

            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(248, 248, 248)'
                }
            ],
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            }
        )
        ]),
        dcc.Tab(label='Find An Employee The Right Position', children=[
            html.H1(children='RBI Succession Planning System', className='six columns'),

            html.Br(),

            html.H4("Please choose the target employee:"),
            dcc.Dropdown(id="slct_employee",
                         options=employee_option,
                         multi=False,
                         searchable=True,
                         placeholder="Target Employee"
                         ),

            html.Br(),

            html.H4("Please select time scale:"),
            dcc.Dropdown(id="slct_time_scale_position",
                         options=[
                             {'label': 'Ready Now', 'value': 'Ready Now'},
                             {'label': 'Ready Soon', 'value': 'Ready Soon'},
                             {'label': 'Ready Later', 'value': 'Ready Later'}
                         ],
                         multi=False,
                         searchable=True,
                         placeholder="Time Scale"
                         ),

            html.Br(),

            html.H4("Please select relevant position preferences:"),

            dcc.Dropdown(id="slct_job_profile_pay_band",
                         options=employee_level_option,
                         multi=True,
                         searchable=True,
                         placeholder="Job Profile Pay Band"
                         ),

            html.Br(),

            dcc.Dropdown(id="slct_position_function",
                         options=function_option,
                         multi=True,
                         searchable=True,
                         placeholder="Function"
                         ),

            html.Br(),

            dcc.Dropdown(id="slct_position_location",
                         options=location_option,
                         multi=True,
                         searchable=True,
                         placeholder="Location"
                         ),

            html.Br(),
            html.Br(),
            html.Br(),

            dash_table.DataTable(
                id='output3',
                columns=[{"name": i, "id": i} for i in talent_pool[
                    ['Unique ID', "Employee Level", "9Box Score", "Previous 9Box Score", "Mobility",
                     "Employee Preference", "Position Text", "Job Profile Pay Band", "Location", "Organization", "Function",
                     'Time in Position (months)', 'Time in Level (months)', 'Time in Company (years)',
                     'Quantitative', 'Analytical', 'Conceptual', 'Communications', 'Working with Others',
                     'Influence & Negotiation', 'Work Management', 'People Management',
                     'Inspiring Leadership', 'Company', 'Industry Knowledge', 'General Business Knowledge',
                     'Functional Expertise', 'Mentoring']].columns],
                data=talent_pool[
                    ['Unique ID', "Employee Level", "9Box Score", "Previous 9Box Score", "Mobility",
                     "Employee Preference", "Position Text", "Job Profile Pay Band", "Location", "Organization", "Function",
                     'Time in Position (months)', 'Time in Level (months)', 'Time in Company (years)',
                     'Quantitative', 'Analytical', 'Conceptual', 'Communications', 'Working with Others',
                     'Influence & Negotiation', 'Work Management', 'People Management',
                     'Inspiring Leadership', 'Company', 'Industry Knowledge', 'General Business Knowledge',
                     'Functional Expertise', 'Mentoring']].to_dict('records'),
                export_format="csv",

                style_cell={
                    'font_family': 'arial',
                    'font_size': '14px',
                    'text_align': 'left'
                },

                style_table={'overflowX': 'auto'},

                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'rgb(248, 248, 248)'
                    }
                ],
                style_header={
                    'backgroundColor': 'rgb(230, 230, 230)',
                    'fontWeight': 'bold'
                }
            ),

            html.Br(),
            html.Br(),
            html.Br(),

            dash_table.DataTable(
                id='output4',
                columns=[{"name": i, "id": i} for i in position_pool[
                    ['Position', "Position Text", "Manager Unique ID", "Job Profile", "Job Profile Pay Band",
                     "Job Family Group", "Company Code", "Location", "Organization", "Function", "Department",
                     "Specialist / Generalist", "Qualification/Certification?", 'Quantitative', 'Analytical',
                     'Conceptual', 'Communications', 'Working with Others', 'Influence & Negotiation',
                     'Work Management', 'People Management', 'Inspiring Leadership', 'Company',
                     'Industry Knowledge', 'General Business Knowledge', 'Functional Expertise',
                     'Mentoring', 'Sum of Weighted Differences', 'Sum of Weighted Differences (Absolute)']].columns],
                data=position_pool[
                    ['Position', "Position Text", "Manager Unique ID", "Job Profile", "Job Profile Pay Band",
                     "Job Family Group", "Company Code", "Location", "Organization", "Function", "Department",
                     "Specialist / Generalist", "Qualification/Certification?", 'Quantitative', 'Analytical',
                     'Conceptual', 'Communications', 'Working with Others', 'Influence & Negotiation',
                     'Work Management', 'People Management', 'Inspiring Leadership', 'Company',
                     'Industry Knowledge', 'General Business Knowledge', 'Functional Expertise',
                     'Mentoring', 'Sum of Weighted Differences', 'Sum of Weighted Differences (Absolute)']].to_dict('records'),
                export_format="csv",

                style_cell={
                    'font_family': 'arial',
                    'font_size': '14px',
                    'text_align': 'left'
                },

                style_table={'overflowX': 'auto'},

                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'rgb(248, 248, 248)'
                    }
                ],
                style_header={
                    'backgroundColor': 'rgb(230, 230, 230)',
                    'fontWeight': 'bold'
                }
            )
        ]),
    ])
])

# ------------------------------------------------------------------------------
# Connect the Plotly graphs with Function
@app.callback(
    [Output("output1", "data"),
    Output("output2", "data"),
    Output("output3", "data"),
    Output("output4", "data")],
    Input("slct_position", "value"),
    Input("slct_time_scale_employee", "value"),
    Input("slct_employee_level", "value"),
    Input("slct_employee_function", "value"),
    Input("slct_employee_location", "value"),
    Input("slct_9box", "value"),
    Input("tip", "value"),
    Input("til", "value"),
    Input("slct_employee", "value"),
    Input("slct_time_scale_position", "value"),
    Input("slct_job_profile_pay_band", "value"),
    Input("slct_position_function", "value"),
    Input("slct_position_location", "value"),
)

def final_output(slct_position, slct_time_scale_employee, slct_employee_level, slct_employee_function, slct_employee_location, slct_9box, tip, til,
                 slct_employee, slct_time_scale_position, slct_job_profile_pay_band, slct_position_function, slct_position_location):

    output1 = find_position(slct_position)
    df = calculateScore_position(slct_position, talent_pool)
    output2 = filter_employees(df, slct_time_scale_employee, slct_position, slct_employee_level, slct_employee_function, slct_employee_location, slct_9box, tip, til)

    output3 = find_employee(slct_employee)
    df2 = calculateScore_employee(slct_employee, position_pool)
    output4 = filter_positions(df2, slct_time_scale_position, slct_employee, slct_job_profile_pay_band, slct_position_function, slct_position_location)
    return [output1, output2, output3, output4]

def find_position(slct_position):
    try:
        position = position_pool.loc[position_pool['Position Key'] == slct_position]
        position = position[['Position', "Position Text", "Manager Unique ID", "Job Profile", "Job Profile Pay Band",
                             "Job Family Group", "Company Code", "Location", "Organization", "Function", "Department",
                             "Specialist / Generalist", "Qualification/Certification?",
                             'Quantitative', 'Analytical', 'Conceptual', 'Communications', 'Working with Others',
                             'Influence & Negotiation', 'Work Management', 'People Management',
                             'Inspiring Leadership', 'Company', 'Industry Knowledge', 'General Business Knowledge',
                             'Functional Expertise', 'Mentoring']]
        position[['Quantitative', 'Analytical', 'Conceptual', 'Communications', 'Working with Others',
                             'Influence & Negotiation', 'Work Management', 'People Management',
                             'Inspiring Leadership', 'Company', 'Industry Knowledge', 'General Business Knowledge',
                             'Functional Expertise', 'Mentoring']]=position[['Quantitative', 'Analytical', 'Conceptual', 'Communications', 'Working with Others',
                             'Influence & Negotiation', 'Work Management', 'People Management',
                             'Inspiring Leadership', 'Company', 'Industry Knowledge', 'General Business Knowledge',
                             'Functional Expertise', 'Mentoring']]+position['Job Profile Pay Band'].values[0]-3
    except:
        position = pd.DataFrame(
            columns=['Position', "Position Text", "Manager Unique ID", "Job Profile", "Job Profile Pay Band",
                     "Job Family Group", "Company Code", "Location", "Organization", "Function", "Department",
                     "Specialist / Generalist", "Qualification/Certification?",
                     'Quantitative', 'Analytical', 'Conceptual', 'Communications', 'Working with Others',
                     'Influence & Negotiation', 'Work Management', 'People Management',
                     'Inspiring Leadership', 'Company', 'Industry Knowledge', 'General Business Knowledge',
                     'Functional Expertise', 'Mentoring'])
    return position.to_dict('records')

def calculateScore_position(slct_position, talent_pool):
    try:
        # find the job profile of the target position
        target_signature = target[target['Position Key'] == slct_position]["Job Profile"].reset_index(drop=True)[0]
        df_target = job_signatures.loc[job_signatures['Job Profile Name'] == target_signature]
        df_target = df_target.drop(columns=['Job Profile Name', 'Job Code', 'Department', 'Job Family Group',
                                            'Specialist / Generalist', 'Qualification/Certification?', 'Market Definition',
                                            'Knowledge Creator'])

        df_talent = talent_pool.loc[(talent_pool['Employee Level'] >= 0)]
        talent_info = df_talent[['Unique ID', 'Employee Level', '9Box Score', 'Position Text', 'Mobility', 'Employee Preference',
                        'Location', 'Function', 'Time in Position (months)', 'Time in Level (months)', 'Time in Company (years)']]

        function = target[target['Position Key'] == slct_position]["Function"].reset_index(drop=True)[0]
        if function == "Tax":
            function = "Finance"
        if function == "Accounting":
            function = "Finance"
        if function == "Coffee":
            function = "Culinary"
        if function == "Facilities":
            function = "People"
        if function == "Global Development":
            function = "Development"
        target_function = time_in_function[time_in_function['Function'] == function][["Unique ID", 'Time in Function (years)', 'Time in Function Weighted (years)']]
        talent_info = talent_info.merge(target_function, how='left', on='Unique ID')

        # adjust weights of the performance scores
        adjusted_target = adjust_scores(df_target).drop(columns=['Job Grade'])
        df_talent = df_talent[
             ['Employee Level', 'Quantitative', 'Analytical', 'Conceptual', 'Communications', 'Working with Others',
             'Influence & Negotiation', 'Work Management', 'People Management',
             'Inspiring Leadership', 'Company', 'Industry Knowledge', 'General Business Knowledge',
             'Functional Expertise', 'Mentoring']]
        df_talent = adjust_scores(df_talent).drop(columns=['Employee Level'])

        # Calculate differences and adjust weights
        df_target = df_target.replace([2], 1)
        df_target = df_target.replace([1], 0.5)
        df_target = df_target.drop(columns=['Job Grade'])

        diff = adjusted_target.values.squeeze() - df_talent
        weighted_diff = diff * df_target.values.squeeze()
        df_talent['Sum of Weighted Differences'] = weighted_diff.sum(axis=1)
        weighted_diff_abs = diff.abs() * df_target.values.squeeze()
        df_talent['Sum of Weighted Differences (Absolute)'] = weighted_diff_abs.sum(axis=1)

        df_talent = talent_info.merge(df_talent, left_index=True, right_index=True)
        df_talent = df_talent.sort_values('Sum of Weighted Differences')
        df_talent.dropna(subset=['Communications'], inplace=True)

    except:
        df_talent = pd.DataFrame(columns = ['Unique ID', "Employee Level", "9Box Score", 'Position Text', "Mobility", "Employee Preference", "Location", "Function", "Time in Position (months)", "Time in Level (months)", "Time in Company (years)",
                              'Quantitative', 'Analytical', 'Conceptual', 'Communications', 'Working with Others',
                              'Influence & Negotiation', 'Work Management', 'People Management',
                              'Inspiring Leadership', 'Company', 'Industry Knowledge', 'General Business Knowledge',
                              'Functional Expertise', 'Mentoring', 'Sum of Weighted Differences', 'Sum of Weighted Differences (Absolute)'])
    return df_talent

def adjust_scores(df):
  for row in range(0, df.shape[0]):
    for col in range(1, df.shape[1]):
      df.iloc[row, col] = df.iloc[row,0] + (df.iloc[row,col]-3)
  return df

def filter_employees(df, slct_time_scale_employee, slct_position, slct_employee_level, slct_employee_function, slct_employee_location, slct_9box, tip, til):
    if slct_time_scale_employee is not None:
        job_profile_pay_band = target[target['Position Key'] == slct_position]["Job Profile Pay Band"].values[0]
        if slct_time_scale_employee == "Ready Now":
            df = df.loc[(df['Employee Level'] >= job_profile_pay_band-2) & (df['Employee Level'] <= job_profile_pay_band + 1)]
        if slct_time_scale_employee == "Ready Soon":
            if job_profile_pay_band == 1:
                df = df.loc[(df['Employee Level'] == 0)]
            if job_profile_pay_band == 2:
                df = df.loc[(df['Employee Level'] >= 0) & (df['Employee Level'] <= 1)]
            if job_profile_pay_band == 3:
                df = df.loc[(df['Employee Level'] >= 0) & (df['Employee Level'] <= 2)]
            if job_profile_pay_band == 4:
                df = df.loc[(df['Employee Level'] >= 1) & (df['Employee Level'] <= 3)]
            if job_profile_pay_band == 5:
                df = df.loc[(df['Employee Level'] >= 2) & (df['Employee Level'] <= 4)]
            if job_profile_pay_band == 6:
                df = df.loc[(df['Employee Level'] >= 4) & (df['Employee Level'] <= 5)]
            if job_profile_pay_band == 7:
                df = df.loc[(df['Employee Level'] >= 5) & (df['Employee Level'] <= 6)]
            if job_profile_pay_band == 8:
                df = df.loc[(df['Employee Level'] == 7)]
            if job_profile_pay_band == 9:
                df = df.loc[(df['Employee Level'] == 8)]
            if job_profile_pay_band == 10:
                df = df.loc[(df['Employee Level'] == 9)]
            if job_profile_pay_band == 12:
                df = df.loc[(df['Employee Level'] == 10)]
        if slct_time_scale_employee == "Ready Later":
            if job_profile_pay_band == 1:
                df = df.loc[(df['Employee Level'] == 0)]
            if job_profile_pay_band == 2:
                df = df.loc[(df['Employee Level'] == 0)]
            if job_profile_pay_band == 3:
                df = df.loc[(df['Employee Level'] == 0)]
            if job_profile_pay_band == 4:
                df = df.loc[(df['Employee Level'] >= 0) & (df['Employee Level'] <= 1)]
            if job_profile_pay_band == 5:
                df = df.loc[(df['Employee Level'] >= 1) & (df['Employee Level'] <= 2)]
            if job_profile_pay_band == 6:
                df = df.loc[(df['Employee Level'] >= 2) & (df['Employee Level'] <= 4)]
            if job_profile_pay_band == 7:
                df = df.loc[(df['Employee Level'] >= 4) & (df['Employee Level'] <= 5)]
            if job_profile_pay_band == 8:
                df = df.loc[(df['Employee Level'] >= 6) & (df['Employee Level'] <= 7)]
            if job_profile_pay_band == 9:
                df = df.loc[(df['Employee Level'] >= 7) & (df['Employee Level'] <= 8)]
            if job_profile_pay_band == 10:
                df = df.loc[(df['Employee Level'] >= 8) & (df['Employee Level'] <= 9)]
            if job_profile_pay_band == 12:
                df = df.loc[(df['Employee Level'] >= 9) & (df['Employee Level'] <= 10)]
    else:
        df = df.loc[df['Employee Level'] <0]
    if slct_employee_level is not None:
        if len(slct_employee_level) > 0:
            df = df.loc[df['Employee Level'].isin(slct_employee_level)]
        else:
            df = df.loc[df['Employee Level'].isin(employee_level_list)]
    if slct_employee_function is not None:
        if len(slct_employee_function) > 0:
            df = df.loc[df['Function'].isin(slct_employee_function)]
        else:
            df = df.loc[df['Function'].isin(function_list)]
    if slct_employee_location is not None:
        if len(slct_employee_location) > 0:
            df = df.loc[df['Location'].isin(slct_employee_location)]
        else:
            df = df.loc[df['Location'].isin(location_list)]
    if slct_9box is not None:
        if len(slct_9box) > 0:
            df = df.loc[df['9Box Score'].isin(slct_9box)]
        else:
            df = df.loc[df['9Box Score'].isin([1, 2, 3, 4, 5, 6, 7, 8, 9])]
    if tip is not None:
        df = df.loc[df['Time in Position (months)'] >= tip]
    if til is not None:
        df = df.loc[df['Time in Level (months)'] >= til]

    return df.to_dict('records')

def find_employee(slct_employee):
    try:
        employee = talent_pool.loc[talent_pool['Unique ID'] == slct_employee]
        employee = employee[['Unique ID', "Employee Level", "9Box Score", "Previous 9Box Score", "Mobility",
                     "Employee Preference", "Position Text", "Job Profile Pay Band", "Location", "Organization", "Function",
                     'Time in Position (months)', 'Time in Level (months)', 'Time in Company (years)',
                     'Quantitative', 'Analytical', 'Conceptual', 'Communications', 'Working with Others',
                     'Influence & Negotiation', 'Work Management', 'People Management',
                     'Inspiring Leadership', 'Company', 'Industry Knowledge', 'General Business Knowledge',
                     'Functional Expertise', 'Mentoring']]
        employee[['Quantitative', 'Analytical', 'Conceptual', 'Communications', 'Working with Others',
                             'Influence & Negotiation', 'Work Management', 'People Management',
                             'Inspiring Leadership', 'Company', 'Industry Knowledge', 'General Business Knowledge',
                             'Functional Expertise', 'Mentoring']]=employee[['Quantitative', 'Analytical', 'Conceptual', 'Communications', 'Working with Others',
                             'Influence & Negotiation', 'Work Management', 'People Management',
                             'Inspiring Leadership', 'Company', 'Industry Knowledge', 'General Business Knowledge',
                             'Functional Expertise', 'Mentoring']]+employee['Employee Level'].values[0]-3
    except:
        employee = pd.DataFrame(
            columns=['Unique ID', "Employee Level", "9Box Score", "Previous 9Box Score", "Mobility",
                     "Employee Preference", "Position Text", "Job Profile Pay Band", "Location", "Organization", "Function",
                     'Time in Position (months)', 'Time in Level (months)', 'Time in Company (years)',
                     'Quantitative', 'Analytical', 'Conceptual', 'Communications', 'Working with Others',
                     'Influence & Negotiation', 'Work Management', 'People Management',
                     'Inspiring Leadership', 'Company', 'Industry Knowledge', 'General Business Knowledge',
                     'Functional Expertise', 'Mentoring'])
    return employee.to_dict('records')

def calculateScore_employee(slct_employee, position_pool):
    try:
        # find the job profile of the target position
        df_employee = talent.loc[talent['Unique ID'] == slct_employee]
        df_employee = df_employee.drop(columns=['Unique ID', '9box Score (box number 1-9)', 'Previous 9Box Score',
                                                'Knowledge Creator', 'Mobility', 'Employee Preference'])

        employee_level = talent[talent['Unique ID'] == slct_employee]["Employee Level"].values[0]
        df_position = position_pool.loc[position_pool['Job Profile Pay Band'] >= employee_level]
        position_info = df_position[['Position', "Position Text", "Manager Unique ID", "Job Profile", "Job Profile Pay Band",
                                    "Job Family Group", "Company Code", "Location", "Organization", "Function", "Department",
                                    "Specialist / Generalist", "Qualification/Certification?"]]

        # adjust weights of the performance scores and calculate differences
        adjusted_employee = adjust_scores(df_employee).drop(columns=['Employee Level'])
        df_position = df_position[
             ['Job Profile Pay Band', 'Quantitative', 'Analytical', 'Conceptual', 'Communications',
              'Working with Others', 'Influence & Negotiation', 'Work Management', 'People Management',
              'Inspiring Leadership', 'Company', 'Industry Knowledge', 'General Business Knowledge',
              'Functional Expertise', 'Mentoring']]
        df_position = adjust_scores(df_position).drop(columns=['Job Profile Pay Band'])

        # calculate differences and adjust weight
        df_employee = df_employee.replace([2], 1)
        df_employee = df_employee.replace([1], 0.5)
        df_employee = df_employee.drop(columns=['Employee Level'])

        diff = adjusted_employee.values.squeeze() - df_position
        weighted_diff = diff * df_employee.values.squeeze()
        df_position['Sum of Weighted Differences'] = weighted_diff.sum(axis=1)
        weighted_diff_abs = diff.abs() * df_employee.values.squeeze()
        df_position['Sum of Weighted Differences (Absolute)'] = weighted_diff_abs.sum(axis=1)

        df_position = position_info.merge(df_position, left_index=True, right_index=True)
        df_position = df_position.sort_values('Sum of Weighted Differences', ascending=False)
        df_position.dropna(subset=['Communications'], inplace=True)
    except:
        df_position = pd.DataFrame(columns = ['Position', "Position Text", "Manager Unique ID", "Job Profile", "Job Profile Pay Band",
                     "Job Family Group", "Company Code", "Location", "Organization", "Function", "Department",
                     "Specialist / Generalist", "Qualification/Certification?", 'Quantitative', 'Analytical',
                     'Conceptual', 'Communications', 'Working with Others', 'Influence & Negotiation',
                     'Work Management', 'People Management', 'Inspiring Leadership', 'Company',
                     'Industry Knowledge', 'General Business Knowledge', 'Functional Expertise',
                     'Mentoring', 'Sum of Weighted Differences', 'Sum of Weighted Differences (Absolute)'])
    return df_position

def filter_positions(df2, slct_time_scale_position, slct_employee, slct_job_profile_pay_band, slct_position_function, slct_position_location):
    if slct_time_scale_position is not None:
        employee_level = talent[talent['Unique ID'] == slct_employee]["Employee Level"].values[0]
        if slct_time_scale_position == "Ready Now":
            df2 = df2.loc[(df2['Job Profile Pay Band'] >= employee_level) & (df2['Job Profile Pay Band'] <= employee_level + 2)]
        if slct_time_scale_position == "Ready Soon":
            if employee_level == 1:
                df2 = df2.loc[(df2['Job Profile Pay Band'] >= 2) & (df2['Job Profile Pay Band'] <= 4)]
            if employee_level == 2:
                df2 = df2.loc[(df2['Job Profile Pay Band'] >= 3) & (df2['Job Profile Pay Band'] <= 4)]
            if employee_level == 3:
                df2 = df2.loc[(df2['Job Profile Pay Band'] >= 4) & (df2['Job Profile Pay Band'] <= 5)]
            if employee_level == 4:
                df2 = df2.loc[(df2['Job Profile Pay Band'] >= 4) & (df2['Job Profile Pay Band'] <= 5)]
            if employee_level == 5:
                df2 = df2.loc[(df2['Job Profile Pay Band'] >= 5) & (df2['Job Profile Pay Band'] <= 6)]
            if employee_level == 6:
                df2 = df2.loc[(df2['Job Profile Pay Band'] >= 6) & (df2['Job Profile Pay Band'] <= 7)]
            if employee_level == 7:
                df2 = df2.loc[(df2['Job Profile Pay Band'] >= 7) & (df2['Job Profile Pay Band'] <= 8)]
            if employee_level == 8:
                df2 = df2.loc[(df2['Job Profile Pay Band'] >= 8) & (df2['Job Profile Pay Band'] <= 9)]
            if employee_level == 9:
                df2 = df2.loc[(df2['Job Profile Pay Band'] >= 9) & (df2['Job Profile Pay Band'] <= 10)]
            if employee_level == 10:
                df2 = df2.loc[(df2['Job Profile Pay Band'] >= 10) & (df2['Job Profile Pay Band'] <= 12)]
            if employee_level == 12:
                df2 = df2.loc[(df2['Job Profile Pay Band'] == 12)]
        if slct_time_scale_position == "Ready Later":
            if employee_level == 1:
                df2 = df2.loc[(df2['Job Profile Pay Band'] >= 4) & (df2['Job Profile Pay Band'] <= 5)]
            if employee_level == 2:
                df2 = df2.loc[(df2['Job Profile Pay Band'] >= 4) & (df2['Job Profile Pay Band'] <= 5)]
            if employee_level == 3:
                df2 = df2.loc[(df2['Job Profile Pay Band'] >= 5) & (df2['Job Profile Pay Band'] <= 6)]
            if employee_level == 4:
                df2 = df2.loc[(df2['Job Profile Pay Band'] >= 5) & (df2['Job Profile Pay Band'] <= 6)]
            if employee_level == 5:
                df2 = df2.loc[(df2['Job Profile Pay Band'] >= 6) & (df2['Job Profile Pay Band'] <= 7)]
            if employee_level == 6:
                df2 = df2.loc[df2['Job Profile Pay Band'] == 7]
            if employee_level == 7:
                df2 = df2.loc[df2['Job Profile Pay Band'] == 8]
            if employee_level == 8:
                df2 = df2.loc[df2['Job Profile Pay Band'] == 9]
            if employee_level == 9:
                df2 = df2.loc[df2['Job Profile Pay Band'] == 10]
            if employee_level == 10:
                df2 = df2.loc[df2['Job Profile Pay Band'] == 12]
            if employee_level == 12:
                df2 = df2.loc[df2['Job Profile Pay Band'] == 12]
    else:
        df2 = df2.loc[df2['Job Profile Pay Band'] < 0]

    if slct_job_profile_pay_band is not None:
        if len(slct_job_profile_pay_band) > 0:
            df2 = df2.loc[df2['Job Profile Pay Band'].isin(slct_job_profile_pay_band)]
        else:
            df2 = df2.loc[df2['Job Profile Pay Band'].isin(job_profile_pay_band_list)]
    if slct_position_function is not None:
        if len(slct_position_function) > 0:
            df2 = df2.loc[df2['Function'].isin(slct_position_function)]
        else:
            df2 = df2.loc[df2['Function'].isin(function_list)]
    if slct_position_location is not None:
        if len(slct_position_location) > 0:
            df2 = df2.loc[df2['Location'].isin(slct_position_location)]
        else:
            df2 = df2.loc[df2['Location'].isin(location_list)]

    return df2.to_dict('records')

if __name__ == '__main__':
    app.run_server(debug=True)





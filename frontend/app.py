from flask import Flask, render_template, request, redirect, url_for
from flask import jsonify
import random


app = Flask(__name__)
users = {}

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users[username] = password 
        #### here I pass data to servvice with logging to chech if user is in database####
        return redirect(url_for('data_selection'))
    return render_template('login.html')

@app.route('/data-selection')
def data_selection():
    return render_template('data_selection.html')

@app.route('/plot-list')
def plot_list():
    return render_template('plot_list.html')

@app.route('/history-of-trades')
def history_of_trades():
    return render_template('history_of_trades.html')

 
data_store = {
    'plot1': [random.randint(0, 50)],
    'plot2': [random.randint(0, 50)], 
    'plot3': [random.randint(0, 50)],
    'plot4': [random.randint(0, 50)],
    'plot5': [random.randint(0, 50)]
}

@app.route('/data-for-plot1')
def data_for_plot1():
    new_data = random.randint(0, 50)
    data_store['plot1'].append(new_data)
    return jsonify({'labels': list(range(len(data_store['plot1']))), 'values': data_store['plot1']})

@app.route('/data-for-plot2')
def data_for_plot2():
    new_data = random.randint(0, 50)
    data_store['plot2'].append(new_data)
    return jsonify({'labels': list(range(len(data_store['plot2']))), 'values': data_store['plot2']})


@app.route('/data-for-plot3')
def data_for_plot3():
    new_data = random.randint(0, 50)
    data_store['plot3'].append(new_data)
    return jsonify({'labels': list(range(len(data_store['plot3']))), 'values': data_store['plot3']})


@app.route('/data-for-plot4')
def data_for_plot4():
    new_data = random.randint(0, 50)
    data_store['plot4'].append(new_data)
    return jsonify({'labels': list(range(len(data_store['plot4']))), 'values': data_store['plot4']})

@app.route('/data-for-plot5')
def data_for_plot5():
    new_data = random.randint(0, 50)
    data_store['plot5'].append(new_data)
    return jsonify({'labels': list(range(len(data_store['plot5']))), 'values': data_store['plot5']})

# data_points = [
#     {"date": "2024-05-01", "name": "Dataset1", "value": 10},
#     {"date": "2024-05-01", "name": "Dataset2", "value": 20},
# ]

# @app.route('/data')
# def get_data():
#     start_date = request.args.get('start_date')
#     end_date = request.args.get('end_date')
#     name = request.args.get('name')

#     filtered_data = # here i have to get data from service
#     labels = [point['date'] for point in filtered_data]
#     values = [point['value'] for point in filtered_data]
#     return jsonify(labels=labels, values=values)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)

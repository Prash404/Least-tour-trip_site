from flask import Flask, render_template, request, redirect, url_for
from threading import Thread
import os

app = Flask(__name__, static_folder='resources')
file_content = ""
file_content2 = ""

#=================================Genetic algorithm machine =================================

def run_GAmachine():
    import requests
    from bs4 import BeautifulSoup
    import numpy as np
    import random

    file_path = './cities.txt'
    try:
        with open(file_path,'r') as file:
            file_content = file.read()
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

    aroute = int(file_content[0])
    file_content = file_content[2:]
    file_content = file_content.replace(' ','')
    file_content = file_content.lower()
    cities = []
    city = ""
    for i in range(len(file_content)):
        if ord(file_content[i])>=97 and ord(file_content[i])<=122:
            city = city + file_content[i]
        else:
            cities.append(city)
            city = ''

    d_matrix=[[0 for city in cities] for city in cities]

    i=0
    j=0
    for i in range(len(cities)):
        for j in range(len(cities)):
            if i==j:
                continue
            elif i>j:
                d_matrix[i][j]=d_matrix[j][i]
                continue
            url = 'https://www.distancecalculator.net/from-'+cities[i]+'-to-'+cities[j]
            response = requests.get(url)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                distance_info = soup.find_all('strong')
                try:
                    val=distance_info[aroute]
                    val=str(val)
                    val=val[8:-20]
                    val=int(val)
                    d_matrix[i][j]=val
                except ValueError as e:
                    if aroute==0:
                        print("Enter the spelling of the cities correctly")
                    else:
                        print("Enter the spelling of the cities correctly or no land route is available")
            else:
                print('Failed to retrieve the webpage')

    num_c = len(d_matrix)
    distance_matrix = np.array(d_matrix)

    #GA parameters
    population_size = 50
    num_generations = 1000
    mutation_rate = 0.1
    crossover_probability = 0.6

    def initialize_population(size, n):
        population = [list(np.random.permutation(range(1, n + 1))) for _ in range(size)]
        return population

    def calculate_total_distance(route):
        total_distance = 0
        for i in range(len(route)):
            total_distance += distance_matrix[route[i] - 1][route[(i + 1) % len(route)] - 1]
        return 1 / total_distance

    def select_parents(population, k=5):
        tournament = random.sample(population, k)
        return max(tournament, key=lambda x: calculate_total_distance(x))

    def crossover(parent1, parent2):
        n = len(parent1)
        start, end = sorted(random.sample(range(n), 2))
        offspring = [-1] * n
        offspring[start:end + 1] = parent1[start:end + 1]
        j = end + 1
        for i in range(end + 1, n + end + 1):
            if parent2[i % n] not in offspring:
                offspring[j % n] = parent2[i % n]
                j += 1
        return offspring

    def mutate(individual):
        if random.random() < mutation_rate:
            i, j = random.sample(range(len(individual)), 2)
            individual[i], individual[j] = individual[j], individual[i]

    population = initialize_population(population_size, num_c)
    for generation in range(num_generations):
        new_population = []
        for _ in range(population_size // 2):
            parent1 = select_parents(population)
            parent2 = select_parents(population)
            if random.random() < crossover_probability:
                offspring1 = crossover(parent1, parent2)
                offspring2 = crossover(parent2, parent1)
            else:
                offspring1, offspring2 = parent1[:], parent2[:]
            mutate(offspring1)
            mutate(offspring2)
            new_population.extend([offspring1, offspring2])
        population = new_population

    best_individual = max(population, key=lambda x: calculate_total_distance(x))
    best_distance = 1 / calculate_total_distance(best_individual)

    optimal_path=[]

    output_file = './output.txt'
    output_file2 = './output2.txt'

    for num in best_individual:
        optimal_path.append(cities[num-1])

    def rotate_array(arr, shift):
        length = len(arr)
        shift = shift % length
        return arr[shift:] + arr[:shift]

    optimal_path = rotate_array(optimal_path, optimal_path.index(cities[0]))

    with open(output_file,'w') as fileo:
        for city in optimal_path:
            fileo.write(city + '->')
        fileo.write("home")
        fileo.write('\n'+"Total Distance (Inverse Cost):%0.2f km" %(best_distance))

    with open(output_file2, 'w') as fileo2:
        for city in optimal_path:
            fileo2.write(city + ", ")
        fileo2.write(optimal_path[0])

#=================================Site backend =================================

@app.route('/')
def index():
    try:
        with open('./output.txt','w') as fileo:
            fileo.write("")
    except FileNotFoundError:
        return "Error404: File not found"
    return render_template('prjhome.html')

@app.route('/save_comment', methods=['POST'])
def save_comment():
    if request.method == 'POST':
        routemethod = request.form.get('Route')
        if routemethod=="Air":
            route = '0'
        else:
            route = '1'
        comment = request.form.get('cities')  
        if comment:
            with open('./cities.txt', 'w') as file: 
                file.write(route+'\n' +comment + '\n')  
            return redirect(url_for('load'))
        else:
            return "No comment provided."
    else:
        return "Invalid request method."

@app.route('/loading')
def load():
    background_thread = Thread(target=run_GAmachine)
    background_thread.start()
    return render_template('loadingscr.html')

@app.route('/output')
def show_output():
    try:
        with open('./output.txt','r') as fileo:
            file_content = fileo.read()
    except FileNotFoundError:
        return "Error404: File not found"
    try:
        with open('./output2.txt','r') as fileo2:
            file_content2 = fileo2.read()
    except FileNotFoundError:
        return "Error404: File not found"
    return render_template('outputpage.html', fileContent = file_content, fileContent2 = file_content2)

@app.route('/check_output')
def check_output():
    if os.path.exists('./output.txt') and os.path.getsize('./output.txt') > 0:
        return '1'
    else:
        return '0'


if __name__ == '__main__':
    app.run(debug=True)
import sys
import math
import random
import csv
import time
"""opens the tsp file "a" and return dictionary 
        -keys are the ID of the city
        -values are the co-ordinates of location of the specific city.
        """
def openfile(a):

    # network of the cities: key=city number , Value = Coordinates
    network = {}

    # open if file exist and reach the data of city and coordinates, record the data into the dictionary
    try:
        f = open(a,'r')
    except FileNotFoundError:
        print("Check the file name again! \nExited")
        exit()
    current_line = f.readline()
    while current_line[0].isalpha():
        current_line = f.readline()
    p = [current_line] + f.readlines()

    # read the lines and use the network to save city and it's coordinates
    for line in p:
        line = line.strip(" ").split()
        network[int(line[0])] = (float(line[1]),float(line[2]))
    f.close()

    return network


"""generate first generation
    generation of size p, for the number of cities defined (1 ... last city number)
    """
def generate_gen(p,number_of_cities):
    one_route = list(range(1,number_of_cities+1))
    generation = [None]*p
    for i in range(p):
        route = random.sample(one_route,number_of_cities)
        route.append(route[0])
        generation[i] = route

    return generation


# Euclidean displacement calculator. From city1 to city2
def euclidean(city1, city2):
    return math.sqrt((city2[0]-city1[0])**2 + (city2[1]-city1[1])**2)


""" Total distance of the route: used as a fitness.
    as the distance shortens, the fitness becomes better.
    """
def total_distance(route, network):
    total = 0
    position = 1
    while position < len(route):
        total += euclidean(network[route[position-1]], network[route[position]])
        position += 1
    return total


"""crossover operator of two point i and j. without loss of generality i<=j
    and two parents will exchange the cities between position i and j.
    City replication is avoided.
    """
def crossover(parent_1, parent_2, number_of_cities):
    # remove the starting point from destination (make it one way)
    parent_1 = parent_1[:-1]
    parent_2 = parent_2[:-1]
    i, j = random.randint(0,number_of_cities-1),random.randint(0,number_of_cities-1)
    if i > j:     # i should be less than or equal to j
        i, j = j,i

    # cities(genes) form parent1 ---> parent2_copy to form offspring2
    parent_1_ItoJ = parent_1[i:j+1]
    # cities(genes) form parent2 ---> parent1_copy to form offspring1
    parent_2_ItoJ = parent_2[i:j+1]

    # to avoid redundance, hashtable is useful for the element look-up.
    set1 = set(parent_1_ItoJ)
    set2 = set(parent_2_ItoJ)

    # copy the cities in each parents which are not found in the intersection part
    # (incoming genes from the other parent should not be redundant in the offspring)
    copy_1 = [city for city in parent_1 if city not in set2]
    copy_2 = [city for city in parent_2 if city not in set1]

    # the crossover material form the other parent will arrive at i to j positions in the parent_copy
    # offsprings are formed from their corresponding parent (the first-copied parent)
    offspring_1 = copy_1[:i] + parent_2_ItoJ + copy_1[i:]
    offspring_2 = copy_2[:i] + parent_1_ItoJ + copy_2[i:]
    offspring_1.append(offspring_1[0])
    offspring_2.append(offspring_2[0])
    return offspring_1, offspring_2


def single_point_crossover(parent1, parent2, number_of_cities):
    i = random.randint(0, number_of_cities-1)
    ran = random.random()
    parent1 = parent1[:-1]
    parent2 = parent2[:-1]
    if ran > 0.5:
        end1 = parent1[i:]
        end2 = parent2[i:]
        set1 = set(end1)
        set2 = set(end2)
        offspring1 = [ele for ele in parent1 if ele not in set2] + end2
        offspring2 = [ele for ele in parent2 if ele not in set1] + end1

    else:
        start1 = parent1[:i]
        start2 = parent2[:i]
        set1 = set(start1)
        set2 = set(start2)
        offspring1 = start2 + [ele for ele in parent1 if ele not in set2]
        offspring2 = start1 + [ele for ele in parent2 if ele not in set1]
    offspring1.append(offspring1[0])
    offspring2.append(offspring2[0])
    return offspring1, offspring2


# do mutation between i and j.
def mutate(route):
    for _ in range(int(0.1*len(route))):
        i, j = random.randint(1, len(route)-3), random.randint(1,len(route)-3)
        route[i], route[j] = route[j], route[i]
    return route


# additional inspection ->>> when there is tangled route
# if we should reverse the route from i to j(if it is shorter that way), reverse it
# to avoid entrapment I used prob to identify the probability of going down the hill
def optimize(route,budget,prob, network):
    for _ in range(budget*len(route)):
        i, j = random.randint(1, len(route)-2), random.randint(1,len(route)-2)
        if i > j:
            i, j = j, i
        dist_to_i = euclidean(network[route[i-1]], network[route[i]])
        dist_from_j = euclidean(network[route[j]], network[route[j+1]])
        dist_to_j = euclidean(network[route[i - 1]], network[route[j]])
        dist_from_i = euclidean(network[route[i]], network[route[j + 1]])
        if dist_to_i + dist_from_j > dist_to_j + dist_from_i:
            route[i:j + 1] = route[i:j + 1][::-1]
        elif (dist_to_j + dist_from_i) / (dist_to_i + dist_from_j) < 1.1 and random.random() < prob:
            route[i:j + 1] = route[i:j + 1][::-1]
    return route


if __name__ == '__main__':
    tspfile = sys.argv[1]
    if len(sys.argv) > 2:
        p = int(sys.argv[2])
        if p==0:
            print("Generation size cannot be ZERO")
            exit()
    else:
        p = 120
    how_long = 150  # Number of generation
    elite_k = 0.4   # the elite parents' percentage in the next generation
    network = openfile(tspfile)  # get the dat from the file
    budget = 7
    prob = 0.05
    number_of_cities = len(network)
    compare = max(1 / number_of_cities, 0.4)  # this determines the probability of optimization
    offsprings_size = int(p*(1-elite_k))
    offsprings_size = offsprings_size - (offsprings_size%2)  # even the number of offspring
    elite_parents_size = p - offsprings_size
    Current_gen = generate_gen(p, number_of_cities)

    thefitness = {}
    for ind, route in enumerate(Current_gen):
        thefitness[total_distance(route, network)] = ind
    for i in range(how_long):
        p = len(Current_gen)
        offsprings = [None] * offsprings_size
        selection_sorted = sorted(thefitness.keys())  # sorted fitness values
        for rep in range(0, offsprings_size, 2):
            e, q = random.randint(0, int(len(thefitness) * 0.5)), random.randint(0, int(0.5 * len(thefitness)))
            curr_parents = Current_gen[thefitness[selection_sorted[e]]], Current_gen[thefitness[selection_sorted[q]]]
            new_borns = crossover(curr_parents[0], curr_parents[1], number_of_cities)
            if random.random() <= 0.1:
                new_borns = mutate(new_borns[0]), mutate(new_borns[1])
            if random.random() <= compare:
                new_borns = optimize(new_borns[0],budget,prob, network), optimize(new_borns[1],budget,prob, network)
            offsprings[rep] = new_borns[0]
            offsprings[rep + 1] = new_borns[1]

        temp_fitness = {}  # temporary fitness to add the fitness of new offspring
        temp_keys = selection_sorted[:elite_parents_size] # select elite parents

        for key in temp_keys:  # find the fit parents and collect their fitness to the next generation fitness pool
            temp_fitness[key] = thefitness[key]

        for fitness in thefitness:  # delete the unfit parents
            if fitness not in temp_keys:
                Current_gen[thefitness[fitness]] = None

        # Find the emptied spot for the new offspring and calculate the fitness
        i = 0
        for r in range(len(Current_gen)):
            route = Current_gen[r]
            if not route:
                route = offsprings[i]
                distance = total_distance(route, network)
                temp_fitness[distance] = r
                Current_gen[r] = route
                i += 1
        # pass the temporary fitness to the next generation fitness.
        thefitness = temp_fitness
    final_answer = min(thefitness)
    print(final_answer)
    file = open('solution.csv', 'w+', newline="")
    with file:
        write = csv.writer(file)
        write.writerows([[i] for i in Current_gen[thefitness[final_answer]]])
    file.close()

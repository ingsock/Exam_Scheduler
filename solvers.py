import random
import math
from typing import List, Set
from scheduler import Schedule, Student, Subject, calculate_penalty


def get_initial_solution(
    subjects: List[Subject], num_days: int, holidays: Set[int]
) -> Schedule:
    """Generates a random initial solution respecting holidays."""
    assignments = {}
    available_days = [d for d in range(num_days) if d not in holidays]
    if not available_days:
        raise ValueError("No available days to schedule exams.")

    for subject in subjects:
        assignments[subject] = random.choice(available_days)
    return Schedule(assignments, num_days)


def simulated_annealing(
    subjects: List[Subject],
    students: List[Student],
    num_days: int,
    holidays: Set[int],
    initial_temp: float = 1000.0,
    cooling_rate: float = 0.995,
    max_iterations: int = 10000,
) -> Schedule:
    current_schedule = get_initial_solution(subjects, num_days, holidays)
    current_cost = calculate_penalty(current_schedule, students)

    best_schedule = current_schedule
    best_cost = current_cost

    temp = initial_temp
    available_days = [d for d in range(num_days) if d not in holidays]

    for _ in range(max_iterations):
        # Neighbor: Move one exam to a random day
        neighbor_assignments = current_schedule.assignments.copy()
        subject_to_move = random.choice(subjects)
        new_day = random.choice(available_days)
        neighbor_assignments[subject_to_move] = new_day
        neighbor_schedule = Schedule(neighbor_assignments, num_days)

        neighbor_cost = calculate_penalty(neighbor_schedule, students)

        # Acceptance probability
        delta = neighbor_cost - current_cost
        if delta < 0 or random.random() < math.exp(-delta / temp):
            current_schedule = neighbor_schedule
            current_cost = neighbor_cost

            if current_cost < best_cost:
                best_schedule = current_schedule
                best_cost = current_cost

        temp *= cooling_rate
        if temp < 0.001:
            break

    return best_schedule


def genetic_algorithm(
    subjects: List[Subject],
    students: List[Student],
    num_days: int,
    holidays: Set[int],
    population_size: int = 50,
    generations: int = 100,
    mutation_rate: float = 0.1,
) -> Schedule:
    available_days = [d for d in range(num_days) if d not in holidays]

    # Initialize population
    population = [
        get_initial_solution(subjects, num_days, holidays)
        for _ in range(population_size)
    ]

    for _ in range(generations):
        # Calculate fitness (minimize penalty)
        # Use 1 / (1 + penalty) as fitness score, avoiding division by zero
        scores = []
        for ind in population:
            penalty = calculate_penalty(ind, students)
            # Handle infinite penalty (hard constraints)
            if penalty == float("inf"):
                scores.append(0.0)
            else:
                scores.append(1.0 / (1.0 + penalty))

        # Check if we have a valid solution at all
        total_score = sum(scores)
        if total_score == 0:
            # Re-initialize population if all are invalid? Or just continue hoping mutation fixes it?
            # Let's keep best ones even if invalid (maybe sort by penalty effectively)
            # Simplified: just proceed.
            pass

        # Selection (Tournament)
        new_population = []
        for _ in range(population_size):
            # Select 2 parents
            parents = random.choices(
                population, weights=scores if total_score > 0 else None, k=2
            )
            p1, p2 = parents[0], parents[1]

            # Crossover
            start = random.randint(0, len(subjects) - 1)
            end = random.randint(start, len(subjects) - 1)

            child_assignments = p1.assignments.copy()
            # Inherit a chunk from p2
            # To be safe, let's use the 'subjects' argument which is a list

            for i in range(start, end + 1):
                subj = subjects[i]
                child_assignments[subj] = p2.assignments[subj]

            # Mutation
            if random.random() < mutation_rate:
                subj_mut = random.choice(subjects)
                child_assignments[subj_mut] = random.choice(available_days)

            new_population.append(Schedule(child_assignments, num_days))

        population = new_population

    # Return best
    best_ind = min(population, key=lambda s: calculate_penalty(s, students))
    return best_ind

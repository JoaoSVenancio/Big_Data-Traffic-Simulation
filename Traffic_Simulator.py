import threading
import time
import random
import psutil


class Car(threading.Thread):
    """
    Class representing a car moving in random directions and interacting with an intersection.
    """
    def __init__(self, car_id, direction, intersection):
        super(Car, self).__init__()
        self.car_id = car_id                        
        self.direction = direction                  
        self.direction_after_intersection = None   
        self.intersection = intersection             
        self.waiting_time = 0                       
        self.is_broken_down = random.random() < 0.1
        self.traffic_light_waiting_time = 0        

    def run(self):
        """
        Method that starts the car's movement and interaction with the intersection.
        """
        print(f'Car {self.car_id} started its route in the direction {self.direction}')   
        movement_time = random.randint(1, 5)                                       
        time.sleep(movement_time)
        print(f'Car {self.car_id} reached the intersection')                          
        self.direction_after_intersection = random.choice(['North', 'South', 'East', 'West'])
        print(f'Car {self.car_id} reached the intersection and will check the traffic light in the direction {self.direction} to move to the direction {self.direction_after_intersection}')
        self.intersection.coordinate_passage(self)                                     


class Intersection:
    """
    Class representing an intersection with a traffic light, coordinating car passage.
    """
    def __init__(self, traffic_light, report_monitor):                            
        self.traffic_light = traffic_light                                                
        self.report_monitor = report_monitor                              
        self.cars_status = {}                                                 
        self.cars_waiting = []                                              
        self.cars_passed = 0                                                
        self.update_event = threading.Event()                                   
        self.cars_on_route = {'North': 0, 'South': 0, 'East': 0, 'West': 0}     
        self.traffic_limit = 2                                              
        self.cars_in_traffic = []                                            
        self.broken_down_cars = []                                              
        
               
    def update_light(self):
        """
        Method that updates the traffic light according to car passage.
        """
        while True:
            if self.cars_passed >= 3:
                # Resets the count of cars passed, updates the traffic light, and displays the current direction
                self.cars_passed = 0
                self.traffic_light.update()
                print(f'\nTraffic light updated. Direction {self.traffic_light.green}')
                
            else:
                # If no cars have passed, waits for the update event or waits for 3 seconds before updating the traffic light
                print(f'\nNo cars have passed. Traffic light updated after 3 seconds')
                self.update_event.wait(timeout=3)
                self.traffic_light.update()
                print(f'\nTraffic light updated. Direction {self.traffic_light.green}')
                self.update_event.clear()

            time.sleep(1)
            
    def coordinate_passage(self, car):
        """
        Method that coordinates a car's passage through the intersection.

        Parameters:
            - car (Car): The car that wants to pass through the intersection.
        """
        with self.traffic_light:
            if car.is_broken_down:
                # If the car is broken down, waits for an additional 2 seconds before proceeding
                print(f'Car {car.car_id} is broken down. Waiting for an additional 2 seconds')
                additional_time = 2
                time.sleep(additional_time)
                car.waiting_time += additional_time
                self.broken_down_cars.append(car)

            # Adds the car to the list of cars waiting at the intersection and increments the count of cars passed
            self.cars_waiting.append(car) 
            self.cars_passed += 1

            # Records the start time of waiting and increments the count of cars on the route        
            start_time = time.time()

            self.cars_on_route[car.direction] += 1

            # Waits until the traffic light allows passage in the direction of the car
            while self.traffic_light.green != car.direction:
                self.traffic_light.condition.wait()

            # Records the end time of waiting and calculates the total waiting time
            end_time = time.time()
            car.traffic_light_waiting_time = int(end_time - start_time)
            print(f'Car {car.car_id} moved after waiting for {car.traffic_light_waiting_time} seconds')

            if self.cars_on_route[car.direction] > self.traffic_limit:
                # Reports heavy traffic if the number of cars on the route exceeds the limit
                print(f'Heavy traffic on the {car.direction} route')
                self.cars_in_traffic.append(car)
            
            # Updates counters, signals to update the traffic light, and notifies other threads
            self.cars_on_route[car.direction] -= 1

            self.update_event.set()
            self.traffic_light.condition.notify_all()

    def report_status(self):
        """
        Method that displays the current status of all cars at the intersection.
        """
        print('\nCars Status:')
        for car in self.cars_waiting:
                status_message = f'Car {car.car_id} came from {car.direction} and proceeded to {car.direction_after_intersection} after the intersection. Waited at the traffic light for {car.traffic_light_waiting_time} seconds'
                # Adds information about heavy traffic and breakdowns, if applicable
                if car in self.cars_in_traffic and car in self.broken_down_cars:
                    status_message += ' - This car encountered traffic - This car broke down'
                elif car in self.cars_in_traffic:
                    status_message += ' - This car encountered traffic'
                elif car in self.broken_down_cars:
                    status_message += ' - This car broke down'
                print(status_message)
            
       
class TrafficLight:
    """
    Class representing a traffic light that controls traffic flow at the intersection.
    """
    def __init__(self):
        self.green = None                                       
        self.mutex = threading.Lock()                           
        self.condition = threading.Condition(self.mutex)        
        self.update_directions = []                             

    def __enter__(self):
        self.mutex.acquire()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.mutex.release()

    def update(self):
        """
        Method that randomly updates the traffic light direction.
        """
        with self.mutex:
            # List of possible directions initially
            possible_directions = ['North', 'South', 'East', 'West']
            # Removes recently updated directions
            for direction in self.update_directions:
                if direction in possible_directions:
                    possible_directions.remove(direction)
            # If all directions have been recently updated, restart the list
            if not possible_directions:
                self.update_directions = []
                possible_directions = ['North', 'South', 'East', 'West']
            # Randomly chooses a new green direction and records the choice    
            self.green = random.choice(possible_directions)
            self.update_directions.append(self.green)
            # Notifies all waiting threads that the traffic light has been updated
            self.condition.notify_all()


class ReportMonitor:
    """
    Class that monitors and displays reports of intersection status.
    """
    def __init__(self):
        self.mutex = threading.Lock()       

    def display_report(self, intersection, execution_time, cpu_usage, memory_usage):
        """
        Method that displays the intersection status report.
        """
        with self.mutex:
            intersection.report_status()   

            # Prints the performance report
            print('\nPerformance Report:')
            print(f'Execution Time: {execution_time} seconds')
            print(f'CPU Usage: {cpu_usage}%')
            print(f'Memory Usage: {memory_usage} MB')

def main():
    """
    Main function that tests the classes with heavy traffic and broken down cars.
    """
    traffic_light = TrafficLight()
    report_monitor = ReportMonitor()
    intersection = Intersection(traffic_light, report_monitor)

    start_time = time.time()

    # Starts a thread to update the traffic light periodically
    update_thread = threading.Thread(target=intersection.update_light, daemon=True)
    update_thread.start()

    # Creates cars and starts their threads
    car_sequence = list(range(1, 13))
    random.shuffle(car_sequence)

    cars = [Car(i, random.choice(['North', 'South', 'East', 'West']), intersection) for i in car_sequence]

    # Starts car threads
    for car in cars:
        car.start()
   
    # Waits for all car threads to finish
    for car in cars:
        car.join()
    
    end_time = time.time()

    # Calculates execution time, CPU usage, and memory usage
    execution_time = end_time - start_time
    cpu_usage = psutil.cpu_percent()
    memory_usage = psutil.virtual_memory().used / (1024 ** 2)        # Memory used in MB

    # Displays the intersection and performance status report using the calculated metrics
    report_monitor.display_report(intersection, execution_time, cpu_usage, memory_usage)

if __name__ == "__main__":
    main()

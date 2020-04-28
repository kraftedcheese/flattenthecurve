from libdw import sm
import random
import matplotlib.pyplot as plt
import numpy as np

#contains population segments, and methods to update these segments
class population:
    def __init__(self):
        #initialise segments of population
        self.N = random.randint(5000000, 6000000) #total population
        self.susceptible = np.array([1 - 1/self.N]) #each segment is as a fraction of the total population
        self.infected = np.array([1/self.N])
        self.quarantined = np.array([0])
        self.dead = np.array([0])
        self.recovered = np.array([0])

        self.q_cap = 15000

        #modifiers -> consider adding to a different class, then have update reference that class
        self.beta = 1.5 #average contact rate in population, try changing in 0.25 intervals: or the force of infection
        self.gamma = 0.05 #recovery rate
        self.q_metric = 0.1 #measure of how effective quarantine measures are
        self.d_rate_i = 0.02 #death rate, not in quarantine
        self.d_rate_q = 0.01 #death rate, in quarantine
    

        self.dt = [0.1] #time interval, the smaller, the better the euler approximation

    def modify(self, env):
        self.q_metric = env.q_metric
        self.healthcare = env.healthcare
        self.beta = 1.5 * (1 - env.sd)

    def update(self):
        #ordinary differential equations modelling changes in each segment as a fraction of the whole population
        for i in range(70):
            self.dR = (self.gamma * self.quarantined[-1]) * self.dt[0]
            self.dQ = (self.q_metric * self.infected[-1] - (self.gamma + self.d_rate_q) * self.quarantined[-1]) * self.dt[0]
            
            if (self.dQ + self.quarantined[-1])*self.N > self.q_cap:
                self.dQ = -(self.gamma + self.d_rate_q) * self.quarantined[-1]
                self.q_sufficient = 0
            else:
                self.q_sufficient = 1

            self.dI = (self.beta * self.susceptible[-1] * self.infected[-1] - self.q_metric * self.infected[-1] * self.q_sufficient - self.d_rate_i * self.infected[-1]) * self.dt[0]
            self.dS = (-1 * self.beta * self.susceptible[-1] * self.infected[-1]) * self.dt[0]
            self.dD = (self.d_rate_i * self.infected[-1] + self.d_rate_q * self.quarantined[-1]) * self.dt[0]

            #calculating the new values for each population segment
            self.s_new = self.susceptible[-1] + self.dS
            self.i_new = self.infected[-1] + self.dI
            self.r_new = self.recovered[-1] + self.dR
            self.q_new = self.quarantined[-1] + self.dQ
            self.d_new = self.dead[-1] + self.dD
            
            #adding the new values to the array
            self.susceptible = np.append(self.susceptible, self.s_new)
            self.infected = np.append(self.infected, self.i_new)
            self.recovered = np.append(self.recovered, self.r_new)
            self.quarantined = np.append(self.quarantined, self.q_new)
            self.dead = np.append(self.dead, self.d_new)

            self.dt.append(self.dt[-1] + self.dt[0])

    def use_actual_pop(self):
        self.actual = np.around(np.array([self.susceptible, self.infected, self.quarantined, self.recovered, self.dead]) * self.N)

    def plot(self):
        self.use_actual_pop()
        plt.plot(self.dt, self.actual[1], label = "infected")
        plt.plot(self.dt, self.actual[2], label = "quarantined")
        plt.plot(self.dt, self.actual[3], label = "recovered")
        plt.plot(self.dt, self.actual[4], label = "dead")
        plt.legend()
        plt.show()

        
    def get_values(self):
        self.use_actual_pop()
        self.templist = [i[-1] for i in self.actual]
        return {"healthy": self.templist[0], "infected": self.templist[1], "quarantined": self.templist[2], "recovered": self.templist[3], "dead": self.templist[4]}

    def get_dead(self):
        return self.dead[-1]
    
    def get_infected(self):
        return self.infected[-1] * self.N

    def get_healthy_prop(self):
        return self.susceptible[-1]

    def __str__(self):
        self.use_actual_pop()
        self.templist = [i[-1] for i in self.actual]
        return "Your citizens are:\n Healthy: {0}, {1} infected, {2} quarantined, {3} recovered, {4} dead.".format(*self.templist)


#contains environmental variables that are player-modifiable
class env:
    def __init__(self):
        self.wealth = 10000
        self.healthcare = 10000
        self.q_metric = 0 #takes a value from 0 to 1, replaces the one used in population
        self.sd = 0 #takes a value from 0 to 2, social distancing value, to replace beta
        self.week = 1
        self.sd_state = "business as usual"

    def get_budget(self):
        self.budget = input("Assign your budget: ")
        self.budget_verified = False
        while self.budget_verified == False:
            if self.budget.isnumeric() == False:
                self.budget = input("Please enter a number for your budget: ")
            elif int(self.budget) > self.wealth:
                self.budget = input("Not enough money! Try again: ")
            else:
                self.budget_verified = True
        self.budget = int(self.budget)
        return self.budget
     
    def improve_healthcare(self):
        self.wealth -= self.budget
        self.healthcare += self.budget

    def social_distancing(self):
        self.sd_verify = False
        while self.sd_verify == False:
            self.sd = input("Choose a level:\n 0: Business as usual\n 1: Circuit breaker\n 2: National emergency\n")
            if self.sd == "0":
                self.sd = 0
                self.sd_state = "business as usual"
                self.sd_verify = True
            elif self.sd == "1":
                self.sd = 0.5
                self.sd_state = "circuit breaker"
                self.sd_verify = True
            elif self.sd == "2":
                self.sd = 0.9
                self.sd_state = "acute bubble tea withdrawal"
                self.sd_verify = True
        return self.sd_state
    
    def improve_contact_tracing(self):
        self.wealth -= self.budget
        self.q_metric += self.budget/500000
        
    def update(self, population):
        self.healthy_prop = population.get_healthy_prop()
        self.wealth += round(100000 * (0.9 - self.sd) * self.healthy_prop)
        self.week += 1
    
    def __str__(self):
        return "Your country has:\n ${0} wealth, {1} healthcare capacity, {2} contact tracing effectiveness.\n It is now in a state of {3}\n This is week {4}.".format(self.wealth, self.healthcare, self.q_metric, self.sd_state, self.week)
 

#implements a state machine to run the game/get inputs
class game(sm.SM):
    start_state = ["start", None, None]

    def get_next_values(self, state, inp):
        if state[0] == "start":
            print()
            next_state = ["player_turn", population(), env()]
            output = """Welcome! You are a newly hired government bureaucrat whose sole purpose is to manage the burgeoning COVID-19 case rate\n 
            Make the appropriate calls at the right times and bring your country past this crisis.\n 
            [Enter]."""

        elif state[0] == "player_turn":
            print(state[1], "\n")
            print(state[2], "\n")
            next_state = ["awaiting_input", state[1], state[2]]
            output = """The following options are available:\n
                [1]: Expand healthcare (uses wealth)\n
                [2]: Increase social distancing (will affect the economy!)\n
                [3]: Improve contact tracing (uses wealth)\n
                [4]: Continue to the next week\n\n Press the appropriate key to continue:"""

        elif state[0] == "awaiting_input" and inp == "1":
            budget = state[2].get_budget()
            state[2].improve_healthcare()
            next_state = ["player_turn", state[1], state[2]]
            output = "Invested ${0} into healthcare".format(budget)
            

        elif state[0] == "awaiting_input" and inp == "2":
            sd = state[2].social_distancing()
            next_state = ["player_turn", state[1], state[2]]
            output = "Your country is in a state of {0}".format(sd)
            
        elif state[0] == "awaiting_input" and inp == "3":
            budget = state[2].get_budget()
            state[2].improve_contact_tracing()
            next_state = ["player_turn", state[1], state[2]]
            output = "Invested ${0} into contact tracing".format(budget)
            
        elif state[0] == "awaiting_input" and inp == "4":
            next_state = ["updating", state[1], state[2]]
            output = "A week passes... [enter]"
        
        elif state[0] == "updating":
            state[1].modify(state[2])
            state[1].update()
            state[2].update(state[1])

            #checks if victory or game over conditions are met
            if state[1].get_dead() > 0.10:
                next_state = ["game_over", state[1], state[2]]
                output = "Game over!"
            elif state[1].get_infected() <= 0.5:
                next_state = ["victory", state[1], state[2]]
                output = "Victory"
            else:
                next_state = ["player_turn", state[1], state[2]]
                output = "Your turn! [enter]"

        elif state[0] == "game_over":
            next_state = ["end", state[1], state[2]]
            output = "You've let too many people die from the outbreak. You're fired!"

        elif state[0] == "victory":
            next_state = ["end", state[1], state[2]]
            output = "You managed to eradicate the virus. Well done!"

        elif state[0] == "end":
            print("You survived {0} weeks".format(state[2].week))
            print("Here are your end-game stats:", state[1])
            state[1].plot()
            next_state = ["end_choice", None, None]
            output = "Do you want to play again? Press y to start and press q to quit"
        
        elif inp == "y" and state[0] == "end_choice":
            next_state = ["start", None, None]
            output = "Here we go again!"

        elif inp == "q":
            next_state = ["terminated", None, None]
            output = "Thanks for playing, stay safe and goodbye!"

        else:
            next_state = [state[0], state[1], state[2]]
            output = "Invalid input. Please try again."

        return next_state, output
    
    #checks if game is continuing
    def cont(self, state):
        if state[0] == "terminated":
            return False
        else:
            return True

#game loop
def run():
    thisgame = game()
    thisgame.start()
    print("Flatten the curve simulator. \n Press enter to continue!")

    while(True):
        if thisgame.cont(thisgame.state):
            keys = input(">>")
            output = thisgame.step(keys)
            print(output)
        else:
            break

    print("Exiting game!")


run()

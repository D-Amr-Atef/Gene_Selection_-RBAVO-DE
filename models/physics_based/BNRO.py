import numpy as np
from copy import deepcopy
from math import gamma
import scipy.stats as ss
from numpy.random import uniform,permutation,rand,standard_normal,normal
from numpy import abs,zeros,ones, clip,log,arange,floor,sum,square,sqrt,eye,matmul,power,diag,argsort,sort,array,matlib,triu,exp,linalg,linspace
from models.root import Root
from copy import deepcopy
from os import getcwd, path, makedirs,remove


class ImprovedBinaryNRO(Root):
    """
    The Binary Improved version of: Nuclear Reaction Optimization Processes (NRO)
    Relief Nuclear Reaction Optimization Processes with DE algorithm
   
    """

   
    ID_POS = 0      # current position
    ID_POS_BIN = 1  # current binary position
    ID_FIT = 2      # current fitness
    ID_kappa = 3
    ID_precision = 4
    ID_recall = 5
    ID_f1_score = 6
    # ID_specificity = 7
    # ID_CCI = 8
    # ID_ICI = 9
    # ID_ROC = 10
    # ID_MCC = 11
    
   
 
    def __init__(self, objective_func=None, transfer_func=None, problem_size=1000, domain_range=(0, 1), log=True,
                 epoch=100, pop_size=10, lsa_epoch=10, seed_num=42):
        
        Root.__init__(self, objective_func, transfer_func, problem_size, domain_range, log, lsa_epoch, seed_num)
        self.epoch = epoch
        self.pop_size = pop_size                
        self.epoch = epoch
        self.pop_size = pop_size
        self.problem_size = problem_size
      
        ###################################################################
        ###################################################################
        self.weighting_factor = 0.8 
        self.crossover_rate = 0.9
        
        ###################################################################
        ###################################################################
  

    def _check_array_equal__(self, array1, array2):
        check = True
        for i in range(len(array1)):
            if array1[i] != array2[i]:
                check = False
                break
        return check

    def _train__(self):
        
      
        pop = [self._create_solution__() for _ in range(self.pop_size)]        
      
        pop, g_best = self._sort_pop_and_get_global_best__(pop=pop, id_fitness=self.ID_FIT, id_best=self.ID_MIN_PROB,apply_DE=True, apply_lsa=True,CR_Rate=self.crossover_rate,W_Factor=self.weighting_factor) 
 
        for epoch in range(self.epoch):
   
            # print("Iteration_Relief_BaseNRO_DE: ", epoch)

            xichma_v = 1
            # Beta = 1.5
            xichma_u = ((gamma(1 + 1.5) * np.sin(np.pi * 1.5 / 2)) / (gamma((1 + 1.5) / 2) * 1.5 * 2 ** ((1.5 - 1) / 2))) ** (1.0 / 1.5)
            levy_b = (np.random.normal(0, xichma_u ** 2)) / (np.abs(np.random.normal(0, xichma_v ** 2)) ** (1.0 / 1.5))
          
            Pb = np.random.uniform()
            Pfi = np.random.uniform()
            freq = 0.05
            alpha = 0.01
            
            ##############################################
            ##############################################
            ##############################################
            # First: NUCLEAR FISSION (NFI) PHASE
            
            for i in range(self.pop_size):

                ## Calculate neutron vector Nei by Eq. (2)
                ## Random 1 more index to select neutron
                temp1 = list( set(range(0, self.pop_size)) - set([i]))
                i1 = np.random.choice(temp1, replace=False)
                
                # Nei: heated neutron is generated by the nuclear fusion of two different random nuclei
                Nei = (pop[i][self.ID_POS] + pop[i1][self.ID_POS]) / 2
                Xi = None
                
                

                ##############################################
                ## Update population of fission products according to Eq.(3), (6) or (9);
                # Pfi is the probability of fission (random number)
                # odd nuclei
                if np.random.uniform() <= Pfi:
                    
                    ##############################################
                    ### Update based on Eq. 3
                    # 1- The creation process of secondary fission (SF) product
                    # Pb is the probability of β decay
                    if np.random.uniform() <= Pb:
                        
                        # Step size
                        xichma1 = (np.log(epoch + 1) * 1.0 / (epoch+1)) * np.abs( np.subtract(pop[i][self.ID_POS], g_best[self.ID_POS]))
                        
                        # Gaussian distribution
                        gauss = np.array([np.random.normal(g_best[self.ID_POS][j], xichma1[j]) for j in range(self.problem_size)])
                        
                        # Fission product nucleus
                        Xi = gauss + np.random.uniform() * g_best[self.ID_POS] - round(np.random.rand() + 1)*Nei
                        
                    ##############################################3    
                    ### Update based on Eq. 6
                    # 2- The creation process of primary fission (PF) product
                    
                    else:
                        # i2: randomly selected from nuclei population
                        i2 = np.random.choice(temp1, replace=False)
                        
                        # Step size
                        xichma2 = (np.log(epoch + 1) * 1.0 / (epoch+1)) * np.abs( np.subtract(pop[i2][self.ID_POS], g_best[self.ID_POS]))
                        
                        # Gaussian distribution                        
                        gauss = np.array([np.random.normal(pop[i][self.ID_POS][j], xichma2[j]) for j in range(self.problem_size)])
                        
                        # Fission product nucleus
                        Xi = gauss + np.random.uniform() * g_best[self.ID_POS] - round(np.random.rand() + 2) * Nei
                
                ##############################################
                ## Update based on Eq. 9
                # An even-even nucleus
                else:
                    # i3: randomly selected from nuclei population
                    i3 = np.random.choice(temp1, replace=False)
                    
                    # Step size
                    xichma2 = (np.log(epoch + 1) * 1.0 / (epoch+1)) * np.abs( np.subtract(pop[i3][self.ID_POS], g_best[self.ID_POS]))
                    
                    # Fission product nucleus
                    Xi = np.array([np.random.normal(pop[i][self.ID_POS][j], xichma2[j]) for j in range(self.problem_size)])

                ##############################################
                Xi = self._amend_solution_random_faster__(Xi)
                temp = self._to_binary_and_update_fit__(Xi, pop[i])
                pop[i] = temp
              
                
              
            ##############################################
            ##############################################
            ##############################################
            # Second: NUCLEAR FUSION (NFU) PHASE
            ##############################################
            ##############################################
            
            
            ## 1- Ionization stage
            ## Calculate the ranked_pop (Pa) through Eq. (10);
            # all nuclei are ranked according to their fitness values
            # ranked_pop: a probability value that obeys uniform distribution
            ranked_pop = ss.rankdata([pop[i][self.ID_FIT] for i in range(self.pop_size)])
            ##############################################
            
            for i in range(self.pop_size):
                X_ion = deepcopy(pop[i][self.ID_POS])
                ##############################################
                # if ranked_pop < rand
                if (ranked_pop[i] * 1.0 / self.pop_size) < np.random.uniform():
                    temp1 = list(set(range(0, self.pop_size)) - set([i]))
                    
                    # Two randomly selected 
                    i1, i2 = np.random.choice(temp1, 2, replace=False)

                    for j in range(self.problem_size):
                        
                        ##############################################
                        #### A- Levy flight strategy is described as Eq. 18
                        # if X(i2) = X(i)
                        if pop[i2][self.ID_POS][j] == pop[i][self.ID_POS][j]:
                            X_ion[j] = pop[i][self.ID_POS][j] + alpha * levy_b * ( pop[i][self.ID_POS][j] - g_best[self.ID_POS][j])
                            
                        ####################################################    
                        #### B- If not, based on Eq. 11, 12
                        else:
                            if np.random.uniform() <= 0.5:
                                X_ion[j] = pop[i1][self.ID_POS][j] + np.random.uniform() * (pop[i2][self.ID_POS][j] - pop[i][self.ID_POS][j])
                            else:
                                X_ion[j] = pop[i1][self.ID_POS][j] - np.random.uniform() * (pop[i2][self.ID_POS][j] - pop[i][self.ID_POS][j])
                
                
                
                ##############################################
                # if ranked_pop >= rand

                else:   
                    
                    ##############################################
                    # Get the worst fission product nucleus
                    X_worst = self._get_global_worst__(pop, self.ID_FIT, self.ID_MAX_PROB)
                    ##############################################
                    
                    for j in range(self.problem_size):
                        
                        ##############################################
                        ##### Based on Eq. 21
                        #### A- Levy flight strategy is described as Eq. 21
                        # if X(worst) = X(best)
                        if X_worst[self.ID_POS][j] == g_best[self.ID_POS][j]:
                            X_ion[j] = pop[i][self.ID_POS][j] + alpha * levy_b * (self.domain_range[1] - self.domain_range[0])
                        
                        ####################################################    
                        ##### B- if not, Based on Eq. 13
                        else:
                            X_ion[j] = pop[i][self.ID_POS][j] + round(np.random.uniform()) * np.random.uniform()*( X_worst[self.ID_POS][j] - g_best[self.ID_POS][j] )

             
                X_ion = self._amend_solution_random_faster__(X_ion)
                temp = self._to_binary_and_update_fit__(X_ion, pop[i])
                pop[i] = temp  


            ##############################################
            ##############################################
            ## 2- Fusion Stage
             
            ##############################################
            ### all ions obtained from ionization are ranked based on (14) - Calculate the Pc through Eq. (14)
            ranked_pop = ss.rankdata([pop[i][self.ID_FIT] for i in range(self.pop_size)])
            ##############################################
            
            for i in range(self.pop_size):

                X_fu = deepcopy(pop[i][self.ID_POS])
                temp1 = list(set(range(0, self.pop_size)) - set([i]))
                
                ##############################################
                # Two randomly selected 
                i1, i2 = np.random.choice(temp1, 2, replace=False)
                
                ##############################################
                #### Generate fusion nucleus
                # the ions of two light nuclei overcome the Coulomb repulsion force
                if (ranked_pop[i] * 1.0 / self.pop_size) < np.random.uniform():
                    t1 = np.random.uniform() * (pop[i1][self.ID_POS] - g_best[self.ID_POS])
                    t2 = np.random.uniform() * (pop[i2][self.ID_POS] - g_best[self.ID_POS])
                    temp2 = pop[i1][self.ID_POS] - pop[i2][self.ID_POS]
                    X_fu = pop[i][self.ID_POS] + t1 + t2 - np.exp(-np.linalg.norm(temp2)) * temp2
               
                ##############################################
                #### Else
                # ions cannot overcome the Coulomb repulsion force and fail to fuse together
                else:
                    
                    ##############################################
                    #### Levy flight strategy is described as Eq. 22
                    ##### Based on Eq. 22
                    # if X(i1) = X(i2)
                    if self._check_array_equal__(pop[i1][self.ID_POS], pop[i2][self.ID_POS]):
                        X_fu = pop[i][self.ID_POS] + alpha * levy_b * (pop[i][self.ID_POS] - g_best[self.ID_POS])
                    
                    ##############################################
                    ##### Based on Eq. 16, 17
                    else:
                        if np.random.uniform() > 0.5:
                            X_fu = pop[i][self.ID_POS] - 0.5*(np.sin(2*np.pi*freq*epoch + np.pi)*(self.epoch - epoch)/self.epoch + 1)*(pop[i1][self.ID_POS] - pop[i2][self.ID_POS])
                        else:
                            X_fu = pop[i][self.ID_POS] - 0.5 * (np.sin(2 * np.pi * freq * epoch + np.pi) * epoch / self.epoch + 1) * (pop[i1][self.ID_POS] - pop[i2][self.ID_POS])

              
                X_fu = self._amend_solution_random_faster__(X_fu)
                temp = self._to_binary_and_update_fit__(X_fu, pop[i])
                pop[i] = temp 
    
         
            pop, g_best = self._sort_pop_and_update_global_best__(pop=pop, id_best=self.ID_MIN_PROB, g_best=g_best,apply_DE=True,apply_lsa=True,CR_Rate=self.crossover_rate,W_Factor=self.weighting_factor) 

            #####################################
    
            self.loss_train.append(g_best[self.ID_FIT])

            #####################################            
            if self.log:
                print("> Epoch: {}, Best fit (Current Run): {}".format(epoch + 1, g_best[self.ID_FIT]))

        print("> Epoch: {}, Best fit (Current Run): {}".format(epoch + 1, g_best[self.ID_FIT]))
          
          #####################################
          
      
            
        return g_best[self.ID_POS_BIN], g_best[self.ID_FIT], self.loss_train, g_best[self.ID_kappa], g_best[self.ID_precision], g_best[self.ID_recall], g_best[self.ID_f1_score]

      
        

"""Optimisation of simulation hyper-parameters"""
import numpy as np, pandas as pd, warnings
import matplotlib.pyplot as plt, seaborn as sns
# Gaussian Processes for Machine Learning (GPML) by Rasmussen and Williams
from sklearn.gaussian_process import GaussianProcessRegressor 
from scipy.stats import norm
# ToDo: One-Hot Encoding fosr Categorical Values

"""
Bayes Theorem: 
    P(A|B) =      P(B|A)   * P(A) where divison by P(B) is omitted (not normalized). P(A|B) is Posterior.
    Posterior = Likelihood * Prior
    P(Objective Function| Data) = P(Data | Objective Function) * P(Objective Function)
    Here the Posterior acts as a SURROGATE for the Objective Function (i.e. how we best understand it)
    Acquisition Function: Used to select next sample of hyper-parameters (based on insights gained about Surrogate)
"""


def objective(x, scale=0.1):
    noise = np.random.normal(loc=0, scale=scale)
    return (x**2 * np.sin(5 * np.pi * x)**6.0) + noise

X = np.arange(0, 1, 0.01) # Domain [0,1]
y, ynoise = [objective(x, 0) for x in X], [objective(x, 0.1) for x in X]
df = pd.DataFrame({"x":X, "y": y, "y+noise": ynoise})

ix = np.argmax(y)
print(f'Global Optima: x={X[ix]:.3f}, y={y[ix]}')

sns.lineplot(data=pd.melt(df, ["x"], value_name="Objective"), x="x", y="Objective", hue="variable", style="variable").set_title("Objective function w./wo. noise")
plt.show()

# Surrogate or approximation for the objective function
def surrogate(model, X):
    # catch any warning generated when making a prediction
    with warnings.catch_warnings():
        # ignore generated warnings
        warnings.simplefilter("ignore")
        return model.predict(X, return_std=True)

# probability of improvement acquisition function
def acquisition(X, Xsamples, model):
    # Calculate the best surrogate score found so far
    yhat, _ = surrogate(model, X)
    best = max(yhat)
    # Calculate mean and stdev via surrogate function
    mu, std = surrogate(model, Xsamples)
    mu = mu[:, 0]
    # Calculate the probability of improvement
    # Can be swapped for Expected Improvement or Lower Confidence Bound
    probs = norm.cdf((mu - best) / (std+1E-9)) # Small number avoids div 0 errors
    return probs

# Optimize the acquisition function
def opt_acquisition(X, y, model):
    # random search, generate random samples
    Xsamples = np.random.random(100)
    Xsamples = Xsamples.reshape(len(Xsamples), 1)
    # calculate the acquisition function for each sample
    scores = acquisition(X, Xsamples, model)
    # Estimates the likelihood that a given candidate sample (input) is worth evaluating with the real objective function.
    # locate the index of the largest scores
    ix = np.argmax(scores)
    return Xsamples[ix, 0]

# Plot real observations vs surrogate function
def plot(X, y, model):
    # Scatter plot of inputs and real objective function
    plt.scatter(X, y, color="red", alpha=0.8)
    # Line plot of surrogate function across domain
    Xsamples = np.asarray(np.arange(0, 1, 0.001))
    Xsamples = Xsamples.reshape(len(Xsamples), 1)
    ysamples, _ = surrogate(model, Xsamples) # Gaussian Process predicts y
    plt.plot(Xsamples, ysamples)
    plt.legend(["Surrogate", "Objective"])
    plt.gca().set(xlabel="x", ylabel="Value", title="Surrogate vs real Objective Function")
    plt.show() # Show the plot

# sample the domain sparsely with noise
X = np.random.random(100)
y = np.asarray([objective(x) for x in X])
# reshape into rows and cols
X = X.reshape(len(X), 1)
y = y.reshape(len(y), 1)
# define the model
model = GaussianProcessRegressor(kernel=None, alpha=1e-10, optimizer='fmin_l_bfgs_b', n_restarts_optimizer=0, normalize_y=False, copy_X_train=True, random_state=0)
# fit the model
model.fit(X, y)
# plot the surrogate function
plot(X, y, model)

# perform the optimization process
for i in range(100):
    # select the next point to sample
    x = opt_acquisition(X, y, model)
    # sample the point
    actual = objective(x)
    # summarize the finding for our own reporting
    est, _ = surrogate(model, [[x]])
    print('>x=%.3f, f()=%3f, actual=%.3f' % (x, est, actual))
    # add the data to the dataset
    X = np.vstack((X, [[x]]))
    y = np.vstack((y, [[actual]]))
    # update the model
    model.fit(X, y)

# plot all samples and the final surrogate function
plot(X, y, model)
# best result
ix = np.argmax(y)
print(f'Best Result: x={X[ix]}, y={y[ix]}')
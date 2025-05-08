import pickle

# Save the entire pickle object
def save_pickle(pickle_object, filename):
    with open(filename, 'wb') as f:
        pickle.dump(pickle_object, f)

# Load the entire pickle object
def load_pickle(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)
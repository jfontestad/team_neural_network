import os, shutil, pickle, shelve
from Bio import SeqIO
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt


def sampling(src, dest, num_samples, seed=42):
    """  
    Sample NUM_SAMPLES of data from SRC and copy them to DEST.
    Set random seed to be SEED.
    """
    np.random.seed(seed)
    all_data_lst = np.array(os.listdir(src))
    n = len(all_data_lst)
    sample_indices = np.random.choice(np.arange(n), num_samples, replace=False)
    sample_files = all_data_lst[sample_indices]

    for file in sample_files:
        shutil.copy(os.path.join(src, file),
                    dest)
    print('copied samples to {}'.format(dest))


def one_hot_encoding(input_folder_path, output_file_path,
                     max_file_num=10000):
    """
    Given the data in INPUT_FOLDER_PATH, encode them and save
    as a buffer called OUTPUT_FILE_PATH.
    
    Note: INPUT_FOLDER_PATH is a directory while OUTPUT_FILE_PATH
          is a file.
    """
    import os
    # Use the following dictionary to perform the transformation
    base_pairs = {'A': [1, 0, 0, 0],
                  'C': [0, 1, 0, 0],
                  'G': [0, 0, 1, 0],
                  'T': [0, 0, 0, 1],
                  'a': [1, 0, 0, 0],
                  'c': [0, 1, 0, 0],
                  'g': [0, 0, 1, 0],
                  't': [0, 0, 0, 1],
                  'n': [0, 0, 0, 0],
                  'N': [0, 0, 0, 0]}

    file_num_limit = max_file_num  # The maximum number of files to be decoded
    file_count = 0

    # Iterate through every file
    all_regions = []
    for file in os.listdir(input_folder_path):
        # When the number of file decoded has reached the limit, stop
        if file_count < file_num_limit:
            data = list(SeqIO.parse(input_folder_path + file, "fasta"))
            for n in range(0, len(data)):
                # Extract the header information
                header = data[n].description.split('|')
                descr = data[n].description
                regionID = header[0]
                expressed = header[1]
                speciesID = header[2]
                strand = header[3]
                # Complement all sequences in the negative DNA strand
                #             if strand == '-':
                #                 # Using the syntax [e for e in base_pairs[n]] to create a new pointer for each position
                #                 one_hot.append([descr, expressed, speciesID, [[e for e in base_pairs[n]] for n in data[n].seq.complement()]])
                #             else:
                all_regions.append([descr, expressed, speciesID, [[e for e in base_pairs[n]] for n in data[n].seq]])
            file_count += 1

    with open(output_file_path, mode="wb") as output:
        print("save to {}".format(output_file_path))
        pickle.dump(all_regions, output)
    return all_regions


def curtail(lst, read_len):
    """ A helper function of get_training_data
    """
    if len(lst) > read_len:
        lst = lst[:read_len]
    else:
        for i in range(read_len - len(lst)):
            lst.append([0, 0, 0, 0])
    return lst


def get_training_data(input_data, output_folder_path,
                      max_len, train_x_name, train_y_name):
    """ 
    Convert INPUT_DATA to ready-to-be-fed training data and 
        corresponding labels.
    Save them to OUTPUT_FOLDER_PATH with name TRAIN_X_NAME and
        TRAIN_Y_NAME.
    INPUT_DATA is directly generated by the function one_hot_encoding. 
    """
    train_x, train_y = [], []
    for region in input_data:
        y, x = int(region[1]), region[3]
        x = curtail(x, max_len)  # Curtail
        x = np.array(x).flatten()  # Flatten
        x = x.reshape((1000, 4))  # Reshape
        train_x.append(x)
        train_y.append(y)

    train_x, train_y = np.array(train_x), np.array(train_y)

    print(train_x.shape, train_y.shape)

    with open(os.path.join(output_folder_path, train_x_name), mode="wb") as output:
        print("save to {}".format(os.path.join(output_folder_path, train_x_name)))
        pickle.dump(train_x, output)

    with open(os.path.join(output_folder_path, train_y_name), mode="wb") as output:
        print("save to {}".format(os.path.join(output_folder_path, train_y_name)))
        pickle.dump(train_y, output)
    return train_x, train_y


def load_data(data_folder_path, train_x_name, train_y_name):
    output_name = train_x_name
    with open(os.path.join(output_folder_path, output_name), 'rb') as file:
        data_x = pickle.load(file)

    output_name = train_y_name
    with open(os.path.join(output_folder_path, output_name), 'rb') as file:
        data_y = pickle.load(file)

    print(data_x.shape, data_y.shape)


def data_split(data_x, data_y, val_split=0.2, seed=42):
    """
    Given totally N data, randomly sample N*VAL_SPLIT of them 
        to form validation data.
    Set random seed to SEED.
    """
    # Split it into training and validation data sets
    N = data_x.shape[0]
    num_val = int(N * val_split)

    np.random.seed(seed)
    val_indices = np.random.choice(np.arange(N), num_val, replace=False)
    train_indices = np.arange(N)[~np.isin(np.arange(N), val_indices)]

    train_x, train_y = data_x[train_indices], data_y[train_indices]
    val_x, val_y = data_x[val_indices], data_y[val_indices]

    print(N, train_x.shape, train_y.shape, val_x.shape, val_y.shape)
    return train_x, train_y, val_x, val_y


def dianostic_plots(train_acc, train_loss, val_train_acc, val_loss):
    """  Plot dianostic plots of a model:
    Plot 1: Traning loss & validation loss against epochs
    Plot 2: Training acc & validation acc against epochs
    """
    epochs = range(1, len(train_acc) + 1)
    
    plt.plot(epochs, train_acc, '-', label='Training train_accuracy')
    plt.plot(epochs, val_train_acc, '-', label='Validation Accuracy')
    plt.title('Training and Validation Accuracy')
    plt.xlabel('epoches')
    plt.legend()

    plt.figure()
    plt.plot(epochs, loss, '-', label='Training Loss')
    plt.plot(epochs, val_loss, '-', label='Validation Loss')
    plt.title('Training and Validation Loss')
    plt.xlabel('epoches')
    plt.legend()

    plt.show()

    
# Define model:
class HybridModel:
    def __init__(self, K, M, input_length, rnn_size, config):
        # Extract configaration of the model:
        pool_size, strides = config['pool_size'], config['strides']
        dr1, dr2 = config['dr1'], config['dr2'] # dropout rates
        d = config['d'] # size of dense layers
        optimizer = config['opt']
        learning_rate = config['learning_rate']
        is_training = config['is_training'] # to control the dropout layers
        
        # Create the placeholders for the inputs:
        self.input = tf.placeholder(tf.float32, shape=[None, input_length, 4])
        self.targets = tf.placeholder(tf.int32, shape=[None, ])
        
        # Define layers for the model:
        self.K = K # number of filters
        
        self.conv = tf.layers.Conv1D(K, M,
                                     strides=1, padding='valid',
                                     use_bias=True, name='conv')
        self.lm_cell_fw = tf.nn.rnn_cell.LSTMCell(num_units = rnn_size, dtype = tf.float32, name='lm_cell_fw')
        self.lm_cell_bw = tf.nn.rnn_cell.LSTMCell(num_units = rnn_size, dtype = tf.float32, name='lm_cell_bw')
        
        # Feed in input
        #print(self.input.shape)
        self.activations = tf.nn.relu(self.conv(self.input))
        #print(self.activations.shape)
        outputs = tf.layers.max_pooling1d(self.activations, 
                                          pool_size=pool_size,
                                          strides=strides)
        outputs = tf.layers.dropout(outputs,
                                    rate=dr1,
                                    training=is_training)
        #print(outputs.shape)
        
        outputs, states = tf.nn.bidirectional_dynamic_rnn(self.lm_cell_fw,
                                                          self.lm_cell_bw,
                                                          outputs, dtype = tf.float32)
        outputs = tf.concat(outputs, axis=2)
        #print(outputs.shape)
        outputs = tf.layers.dropout(outputs,
                                    rate=dr2,
                                    training=is_training)
        
        outputs = tf.nn.relu(tf.layers.dense(outputs, d, name='dense1'))
        #print(outputs.shape)
        output_logits = tf.layers.dense(outputs, 1, name='dense2')
        #print(output_logits.shape)
        
        self.loss = tf.losses.sparse_softmax_cross_entropy(self.targets, output_logits)
        #print(self.loss.shape)
        self.global_step = tf.train.get_or_create_global_step()
        self.train_op = optimizer.minimize(self.loss)
        self.saver = tf.train.Saver()
   
tf.reset_default_graph() # Reset the computational graph before defining a new model.

optimizers = {'adam': tf.train.AdamOptimizer(learning_rate=1e-3),
              'rmsprop': tf.train.RMSPropOptimizer(learning_rate=1e-2)}
opt = optimizers['rmsprop']
model_config = {'pool_size': 5, 'strides': 5, 'dr1': 0.6, 'dr2': 0.7, 'd': 20, 
          'opt': opt, 'learning_rate': 1e-2, 'is_training': True}
model = HybridModel(K=30, M=15, input_length=1028, rnn_size=15, config=model_config)

# Define training function:
def train(model, train_x, train_y, val_x, val_y, config, verbose=True, print_every=10):
    epochs, iteration, output_path = config['epochs'], config['iteration'], config['output_path']
    val_loss_record = []
    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())
        for epoch in range(epochs):
            print("epoch {}".format(epoch))
            for iters in range(iteration):
                # Here is how you obtain a batch:
                batch_size = train_x.shape[0] // iteration
                
                feed = {model.input: train_x, model.targets: train_y}
                model.is_training = True
                step, train_loss, _ = sess.run([model.global_step, model.loss, model.train_op], feed_dict=feed)
                if verbose:
                    if iters % print_every == 0:
                        print("    iteration {}, train_loss: {}".format(iters, train_loss))
            feed = {model.input: val_y, model.targets: val_y}
            model.is_training = False
            val_loss = sess.run([model.loss], feed_dict=feed)
            val_loss_record.append(val_loss)
            print("validation loss: {}".format(val_loss))
        # Here is how you save the model weights
        model.saver.save(sess, output_path)
    return val_loss_record

# Save the model for later analysis
save_model_path = '/home/ubuntu/data/team_neural_network/code/models'
model_name = 'hybrid_net-tensorflow.h5'
output_path = os.path.join(save_model_path, model_name)
training_config = {'epochs': 35, 'iteration': 100, 'output_path': output_path}

val_loss_record = train(model, train_x, train_y, val_x, val_y, training_config)
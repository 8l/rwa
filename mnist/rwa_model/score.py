#!/usr/bin/env python3
##########################################################################################
# Author: Jared L. Ostmeyer
# Date Started: 2017-01-01 (This is my new year's resolution)
# Purpose: Score recurrent neural network on test dataset
# License: For legal information see LICENSE in the home directory.
##########################################################################################

##########################################################################################
# Libraries
##########################################################################################

import os

import numpy as np
import tensorflow as tf
import dataplumbing as dp

##########################################################################################
# Settings
##########################################################################################

# Model settings
#
num_features = dp.test.num_features
max_steps = dp.test.max_length
num_cells = 250
num_classes = dp.test.num_classes
activation = tf.nn.tanh
initialization_factor = 3.0

# Test parameters
#
batch_size = dp.test.num_samples

##########################################################################################
# Model
##########################################################################################

# Inputs
#
x = tf.placeholder(tf.float32, [batch_size, max_steps, num_features])	# Features
l = tf.placeholder(tf.int32, [batch_size])	# Sequence length
y = tf.placeholder(tf.float32, [batch_size, num_classes])	# Labels

# Trainable parameters
#
s = tf.Variable(tf.random_normal([num_cells], stddev=np.sqrt(initialization_factor)))	# Determines initial state

W_g = tf.Variable(
	tf.random_uniform(
		[num_features+num_cells, num_cells],
		minval=-np.sqrt(2.0*initialization_factor/(num_features+2.0*num_cells)),
		maxval=np.sqrt(2.0*initialization_factor/(num_features+2.0*num_cells))
	)
)
b_g = tf.Variable(tf.zeros([num_cells]))
W_u = tf.Variable(
	tf.random_uniform(
		[num_features, num_cells],
		minval=-np.sqrt(2.0*initialization_factor/(num_features+num_cells)),
		maxval=np.sqrt(2.0*initialization_factor/(num_features+num_cells))
	)
)
b_u = tf.Variable(tf.zeros([num_cells]))
W_a = tf.Variable(
	tf.random_uniform(
		[num_features+num_cells, num_cells],
		minval=-np.sqrt(2.0*initialization_factor/(num_features+2.0*num_cells)),
		maxval=np.sqrt(2.0*initialization_factor/(num_features+2.0*num_cells))
	)
)
b_a = tf.Variable(tf.zeros([num_cells]))

W_o = tf.Variable(
	tf.random_uniform(
		[num_cells, num_classes],
		minval=-np.sqrt(2.0*initialization_factor/(num_cells+num_classes)),
		maxval=np.sqrt(2.0*initialization_factor/(num_cells+num_classes))
	)
)
b_o = tf.Variable(tf.zeros([num_classes]))

# Internal states
#
h = tf.zeros([batch_size, num_cells])
n = tf.zeros([batch_size, num_cells])
d = tf.zeros([batch_size, num_cells])

# Define model
#
h += activation(tf.expand_dims(s, 0))

for i in range(max_steps):

	x_step = x[:,i,:]
	xh_join = tf.concat(1, [x_step, h])	# Combine the features and hidden state into one tensor

	g = tf.matmul(xh_join, W_g)+b_g
	u = tf.matmul(x_step, W_u)+b_u
	q = tf.matmul(xh_join, W_a)+b_a

	q_greater = tf.maximum(q, 0.0)	# Greater of the exponent term or zero
	scale = tf.exp(-q_greater)
	a_scale = tf.exp(q-q_greater)

	n = tf.mul(n, scale)+tf.mul(tf.mul(u, tf.nn.tanh(g)), a_scale)	# Numerically stable update of numerator
	d = tf.mul(d, scale)+a_scale	# Numerically stable update of denominator
	h_new = activation(tf.div(n, d))

	h = tf.select(tf.greater(l, i), h_new, h)	# Use new hidden state only if the sequence length has not been exceeded

ly = tf.matmul(h, W_o)+b_o
py = tf.nn.softmax(ly)

##########################################################################################
# Analyzer
##########################################################################################

# Cost function and optimizer
#
cost = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(ly, y))	# Cross-entropy cost function

# Evaluate performance
#
correct = tf.equal(tf.argmax(py, 1), tf.argmax(y, 1))
accuracy = 100.0*tf.reduce_mean(tf.cast(correct, tf.float32))

##########################################################################################
# Score
##########################################################################################

# Operation to initialize session
#
initializer = tf.global_variables_initializer()

# Open session
#
with tf.Session() as session:

	# Initialize variables
	#
	session.run(initializer)

	# Load the trained model
	#
	loader = tf.train.Saver()
	loader.restore(session, 'bin/train.ckpt')

	# Grab the test data
	#
	xs, ls, ys = dp.test.batch(batch_size)
	feed = {x: xs, l: ls, y: ys}

	# Run model
	#
	out = session.run((cost, accuracy), feed_dict=feed)
	print('Dataset:', 'test', 'Cost:', out[0]/np.log(2.0), 'Accuracy:', out[1])


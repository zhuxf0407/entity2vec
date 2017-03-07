import optparse
import os
import codecs
import collections
import numpy as np
from gensim.models import Word2Vec


def get_e2v_embedding(embeddings_file):

	model = Word2Vec.load_word2vec_format(embeddings_file, binary=True)

	return model


def get_e2v_embedding_vector(embedding_model,ID):

	vec = []

	try:
		vec = embedding_model[ID]

	except KeyError:#empty vector if it is not found
		pass

	return vec


def get_items_liked_by_user(training):

	items_liked_by_user_dict = collections.defaultdict(list)

	for line in training:

		line = line.split(' ')

		u = line[0]

		item = line[1]

		relevance = int(line[2])

		if relevance >= 4: #only relevant items are used to compute the similarity

			items_liked_by_user_dict[u].append(item)

	training.seek(0) #we can iterate in the file again

	return items_liked_by_user_dict


def compute_item_similarity(embedding_model,prop,items_liked_by_user,item, num_of_items_liked):

	avg_s = 0

	for past_item in items_liked_by_user:


		try:
			avg_s += embedding_model.similarity(past_item,item)/(num_of_items_liked) #if an item is not found in the embeddings

		except KeyError:

			pass
		
	return avg_s



def feature_generator(embeddings, training, feature_file):

	properties = sorted(os.listdir(embeddings))[0:-1]  #we exclude the user-item, we treat it separately

	with codecs.open(feature_file,'w', encoding='utf-8') as file_write:

		with codecs.open(training,'r', encoding='utf-8') as train:

			items_liked_by_user_dict = get_items_liked_by_user(train) #dictionary [user] : [item1,item2,item3..itemn]

			for i, line in enumerate(train):

				if i > 2765: #resume previous calculation, don't want to start over

					line = line.split(' ')

					user = line[0] #user29

					user_id = int(user.strip('user')) #29

					item = line[1] #http://dbpedia.org/resource/The_Golden_Child

					relevance = int(line[2]) #5

					#binarization of the relevance values
					relevance = 1 if relevance >= 4 else 0

					file_write.write('%d qid:%d' %(relevance,user_id))

					########################
					## collaborative term ##
					########################

					#it can be considered as the first property

					prop = 'feedback'

					print(prop)

					emb = get_e2v_embedding(embeddings+'/'+prop+'/'+os.listdir(embeddings+'/'+prop)[0]) #read the embedding file into memory

					try:
						avg_s = emb.similarity(user,item)

					except KeyError: #the item has never been liked by any user
						avg_s = 0


					file_write.write(' 1:%f ' %avg_s)

					count = 2

	        		########################
	        		## content-based term ##
	        		########################

					items_liked_by_user = items_liked_by_user_dict[user]

					num_of_items_liked = len(items_liked_by_user)

					for prop in properties: #for each property

						emb = get_e2v_embedding(embeddings+'/'+prop+'/'+os.listdir(embeddings+'/'+prop)[0]) #read the property-embedding file into memory

						#item_vec = get_e2v_embedding_vector(emb, item)	#w.r.t to the current property

						if prop == properties[-1]: #last element

							print(prop)

							avg_sim = compute_item_similarity(emb,prop,items_liked_by_user,item, num_of_items_liked)

							file_write.write(' %d:%f # %s\n' %(count,avg_sim,item))
							
						else:

							print(prop)

							avg_sim = compute_item_similarity(emb,prop,items_liked_by_user,item, num_of_items_liked)

							print(avg_sim)

							file_write.write(' %d:%f' %(count,avg_sim))

							count += 1




if __name__ == '__main__':

    parser = optparse.OptionParser()
    parser.add_option('-e','--embeddings', dest = 'embeddings_folder', help = 'embeddings_folder')
    parser.add_option('-o','--output', dest = 'feature_file', help = 'feature_file')
    parser.add_option('-t','--training', dest = 'training_set', help = 'cutting threshold scorers')


    (options, args) = parser.parse_args()

    feature_generator(options.embeddings_folder,options.training_set,options.feature_file)
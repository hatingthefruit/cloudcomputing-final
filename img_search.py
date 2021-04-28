
from mpi4py import MPI
import sys
import hashlib
from os import listdir

#Helper function to split an array up into size number of subarrays. This allows us to divide the files on a host between different 
def split(list_to_split, size):
    k, m = divmod(len(list_to_split), size)
    return list(list_to_split[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(size))


comm = MPI.COMM_WORLD
size = comm.Get_size()
rank = comm.Get_rank()

# Get file from last cmd line argument
img_filepath = sys.argv[-1]

#Define a hasher object
hasher = hashlib.md5()

isFound = False

# Root process will hash the user image
if rank == 0:
	
	with open (str(img_filepath), 'rb') as img_file:
		buf = img_file.read()
		hasher.update(buf)
		
		target_img_hash = hasher.hexdigest()	


# We are worker processes
else:
	target_img_hash = None


# Everybody blocks & gets the img hash to search for.
target_img_hash = comm.bcast(target_img_hash, root=0)
# The host process gathers a list of all hostnames that have processes being run on them
host_list = comm.gather(MPI.Get_processor_name(), root=0)

# Remove duplicates in the list of hostnames, then send it to all processes
if rank == 0:
	host_set = set(host_list)
	host_list = list(host_set)
host_list = comm.bcast(host_list, root=0)

# Add a separate communicator for processes on a single host
host_color = host_list.index(MPI.Get_processor_name())
host_comm = comm.Split(color=host_color)
host_rank = host_comm.Get_rank()

# Get a list of files in some_images dir
root_images_on_vm = []
if host_rank == 0:
	images_on_vm = listdir('./some_images')

	# Prepend the dir path to each image filename
	root_images_on_vm = [f'./some_images/{i}' for i in images_on_vm]
	root_images_on_vm = split(root_images_on_vm, host_comm.Get_size())

# Split up the image files between processes on a single host, to avoid redoing work
images_on_vm = []
images_on_vm = host_comm.scatter(root_images_on_vm, root=0)

# Default value that indicates a process did not find a file
found_image = ['', MPI.Get_processor_name()]

# Loop through all images in the array and try to match the hash with the input file
for each_image in images_on_vm:
	with open (each_image, 'rb') as vm_img_file:
		# Generate the hash for the current file
		hasher = hashlib.md5()
		buf = vm_img_file.read()
		hasher.update(buf)
		vm_img_hash = hasher.hexdigest()

	# the img exists, set the value for found_image to the name of that file and stop searching
	if vm_img_hash == target_img_hash:
		found_image[0] = each_image
		break

# Get the names of images from all the processes
found_ranks = comm.gather(found_image, root=0)

if rank == 0:
	# Print out all the results of the lookup
	for i in range(len(found_ranks)):
		if found_ranks[i][0] != '':
			isFound = True
			print('Image called %s found on host %s with process rank %d' % (found_ranks[i][0], found_ranks[i][1], i))
	if not isFound:
		print('Image was not found on any host')
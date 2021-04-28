


from mpi4py import MPI
import sys
import hashlib
from os import listdir

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


# Everybody blocks & gets the img hash to search for. Then parallel lookup happens after
target_img_hash = comm.bcast(target_img_hash, root=0)
host_list = comm.gather(MPI.Get_processor_name(), root=0)
if rank == 0:
	host_set = set(host_list)
	host_list = list(host_set)
	print(host_list)

host_list = comm.bcast(host_list, root=0)
print(host_list)
host_color = host_list.index(MPI.Get_processor_name())
print(host_color)
host_comm = comm.Split(color=host_color)

host_rank = host_comm.Get_rank()
# Begin lookup for on every process including root
	
# Get a list of files in some_images dir
if host_rank == 0:
	images_on_vm = listdir('./some_images')

	# Prepend the dir path to each image filename
	images_on_vm = [f'./some_images/{i}' for i in images_on_vm]
else:
	images_on_vm = []

print(images_on_vm)
host_comm.Scatter(images_on_vm, images_on_vm, root=0)

found_image = ''

for each_image in images_on_vm:
	with open (each_image, 'rb') as vm_img_file:
		hasher = hashlib.md5()
		buf = vm_img_file.read()
		hasher.update(buf)

		vm_img_hash = hasher.hexdigest()

	# the img exists, notify other processes and break. print out where it was found and where the other processes stopped at
	if vm_img_hash == target_img_hash:
		found_image = each_image
		break

found_ranks = comm.gather(found_image, root=0)

if rank == 0:
	for i in range(len(found_ranks)):
		if found_ranks[i] != '':
			print('Image called %s found in VM with process rank %d' % (found_ranks[i], i))

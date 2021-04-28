


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

# Begin lookup for on every process including root
	
# Get a list of files in some_images dir
images_on_vm = listdir('./some_images')

# Prepend the dir path to each image filename
images_on_vm = [f'./some_images/{i}' for i in images_on_vm]

#comm.Barrier()
# for each image file in the dir on the respective worker VM, calc the hash of it and compare to target hash
for each_image in images_on_vm:

	req = comm.irecv(source=MPI.ANY_SOURCE, tag=1)
	if req.Test() == True:
		print("Process of rank %d stopped searching at file %s\n" % (rank, each_image))
		break
	
	with open (each_image, 'rb') as vm_img_file:
		buf = vm_img_file.read()
		hasher.update(buf)

		vm_img_hash = hasher.hexdigest()

	# the img exists, notify other processes and break. print out where it was found and where the other processes stopped at
	if vm_img_hash == target_img_hash:
		
		isFound = True
		for r in range(size):
			comm.isend(0, dest=r, tag=1)	
		
		print("Image called %s found in VM with process rank %d\n" % (each_image, rank))
		break



if isFound == False:
	print("Image called %s not found anywhere.\n" % (img_filepath))


			



















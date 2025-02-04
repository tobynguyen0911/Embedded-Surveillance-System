
source env/bin/activate
python ECSE488-group/stream.py -c 2 &
chisel client --auth max:chisel maxschaefer.me:12398 R:1111:localhost:5000 R:2222:localhost:22 &

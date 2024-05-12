sleep 10

node_0_ip=$(getent hosts matching_engine_redis_0 | awk '{ print $1 }')
node_1_ip=$(getent hosts matching_engine_redis_1 | awk '{ print $1 }')
node_2_ip=$(getent hosts matching_engine_redis_2 | awk '{ print $1 }')
node_3_ip=$(getent hosts matching_engine_redis_3 | awk '{ print $1 }') # New node
node_4_ip=$(getent hosts matching_engine_redis_4 | awk '{ print $1 }') # New node
node_5_ip=$(getent hosts matching_engine_redis_5 | awk '{ print $1 }') # New node

redis-cli --cluster create \
$node_0_ip:6379 $node_1_ip:6379 $node_2_ip:6379 \
$node_3_ip:6379 $node_4_ip:6379 $node_5_ip:6379 \
--cluster-replicas 1 --cluster-yes

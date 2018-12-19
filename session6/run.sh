#!/bin/bash
#clear

## declare an array variable
declare -a support=(0.01 0.01 0.01 0.01 0.05 0.07 0.2 0.5)
declare -a confidence=(0.01 0.25 0.5 0.75 0.25 0.25 0.25 0.25)

# get length of an array
length=${#support[@]}

# use for loop to read all values and indexes
printf '| %+4s| %+8s| %+10s| %+20s| \n' "Row" "Support" "Confidence" "Nr. of association"
for (( i=0; i<${length}; i++ ));
do
    N_Associations="$(/usr/local/bin/python3 query.py "-s" ${support[$i]} "-c" ${confidence[$i]} | grep -E -o "[0-9]+" | tail -1)"
    printf '| %+4s| %+8s| %+10s| %+20s| \n' $((i+1)) ${support[$i]} ${confidence[$i]} ${N_Associations}
done

echo "********************** Row 4 **********************"
/usr/local/bin/python3 query.py -s 0.01 -c 0.75


echo "********************** Row 5 **********************"
/usr/local/bin/python3 query.py -s 0.05 -c 0.25

echo "********************** Row 6 **********************"
/usr/local/bin/python3 query.py -s 0.07 -c 0.25
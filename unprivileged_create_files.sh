INPUT=$1
cat $INPUT | while read line
do
  if [ ! -z "$line" ]; then
    TARG=`echo $line | awk ' { print $1 } '`
    USER=`echo $line | awk ' { print $2 } '`
    GROUP=`echo $line | awk ' { print $3 } '`
    MOD=`echo $line | awk ' { print $4 } '`
    echo ${USER}:${GROUP} ${TARG}
    SLASH=`printf $TARG | tail -c 1`
    if [[ "${SLASH}" == "/" ]]
      then
        mkdir -p $TARG
      else
        touch $TARG
    fi
    echo ${USER}:${GROUP} ${TARG}
    chown ${USER}:${GROUP} ${TARG}
    chmod ${MOD} ${TARG}
  fi
done

#!/bin/bash -e

# input dir
DIR=txt
# prefix of calendar files
calendar=wartungsplan-03
startDate=2023-10-01
duration=00:30

declare -A rrule=(
	["daily"]="FREQ=DAILY"
	["weekly"]="FREQ=WEEKLY"
	["biweekly"]="FREQ=WEEKLY;INTERVAL=2"
	["monthly"]="FREQ=MONTHLY;BYDAY=1MO"
	["quarterly"]="FREQ=MONTHLY;INTERVAL=3;BYDAY=1MO"
	["yearly"]="FREQ=YEARLY"
)

declare -A startTime=(
	["daily"]="08:00"
	["weekly"]="08:00"
	["biweekly"]="08:00"
	["monthly"]="08:00"
	["quarterly"]="08:00"
	["yearly"]="08:00"
)

function plusMinutes(){
  # in: startTime 14:58
  # in: interval in seconds

  delta=$2

  # given startTime in seconds
  time=$(date -d "1970-01-01 $1:00" +"%s")
  time=$((time + delta))
  echo $(date -d "1970-01-01 00:00:00 UTC $time seconds" +"%H:%M")
}

function addEvent(){
  # in: filename
  # in: interval
  # in: number
  # in: title
  filename=$1

  rr=${rrule[$2]}
  out=$2

  shift 3
  t=$@

  s=${startTime[${wp[0]}]}
  #echo LOG: cat \"$DIR/$filename\" \| addEventToIcal --start-date $startDate --rrule \"$rr\" --start-time $s --duration $duration --title \"$@\" \"$calendar-$out.ics\"
  cat "$DIR/$filename" | addEventToIcal --start-date $startDate --rrule "$rr" --start-time $s --duration $duration --title "$t" "$calendar-$out.ics"
}


# calculate duration (from 20:49 to 1249 s)
d=$(echo $duration|sed 's/\(..\):\(..\)/\1*3600+\2*60/'|bc)
if ! [[ "$d" =~ ^[0-9][0-9]+$ ]]; then echo "ERROR: duration mismatch: $d"; exit 5; fi

# count events
n_events=0

# walk input dir
while read w
do
  echo "    : $w"

  # preserve spaces in filenames
  wt=${w// /\\ }
  # split filename at _
  IFS='_' read -ra wp <<< "${wt%.*}"

  # do the work
  addEvent "$w" ${wp[@]}
  n_events=$((n_events + 1))

  # calculate next start_time
  # (to make calendar look nice for daily events one after the other)
  s=${startTime[${wp[0]}]}
  startTime[${wp[0]}]=$(plusMinutes $s $d)
done < <(ls $DIR)


echo "------------------"
echo "Created $n_events events"
echo "Total events in all $calendar-\*.ics files:"
grep -h "^SUMMARY:" $calendar-*.ics | wc -l

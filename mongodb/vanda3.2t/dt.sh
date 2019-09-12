workloads="load u100 r50_u50 r90_u10"
for wkl in ${workloads};
do
sed -i s/recordcount=1073741824/recordcount=4294967296/ ./tworkload/512B_${wkl}
sed -i s/fieldlength=512/fieldlength=128/ ./tworkload/512B_${wkl}
done


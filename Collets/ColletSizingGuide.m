%%This Script is Used to Calculate the Internal Dimensions of the Collet%%

compression_ratio=pi*d_vial/(pi*8);
mat=[0;0];
d_lower=d_vial-compression_ratio;
d_upper=d_vial+compression_ratio;
mat(1,1)=[d_lower];
mat(2,1)=[d_upper];
mat
/*
 * Standalone temperature logger
 *
 */

#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>
#include "pcsensor.h"

/* Calibration adjustments */
/* See http://www.pitt-pladdy.com/blog/_20110824-191017_0100_TEMPer_under_Linux_perl_with_Cacti/ */
static float scale = 1.0287;
static float offset = -1.85;
int opt;

int main(int argc, char *argv[]){
	opterr = 0;
	char *endptr;
	while((opt = getopt(argc, argv, "o:")) != -1) {
		switch (opt) {
			case 'o':
				offset = offset + strtof(optarg, &endptr);
				break;
		default:
			printf("Usage: %s [-o temp offset]\n",argv[0]);
			break;
		}
	}

	int passes = 0;
	float tempc = 0.0000;
	do {
		usb_dev_handle* lvr_winusb = pcsensor_open();

		if (!lvr_winusb) {
			/* Open fails sometime, sleep and try again */
			sleep(3);
		}
		else {
	
			tempc = pcsensor_get_temperature(lvr_winusb);
			pcsensor_close(lvr_winusb);
		}
		++passes;
	}
	while ((tempc > -0.0001 && tempc < 0.0001) || passes >= 4);

	if (!((tempc > -0.0001 && tempc < 0.0001) || passes >= 4)) {
		/* Apply calibrations */
		tempc = (tempc * scale) + offset;

		printf("%f\n", tempc);
		fflush(stdout);

		return 0;
	}
	else {
		return 1;
	}

}

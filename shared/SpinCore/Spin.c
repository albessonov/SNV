#include <stdio.h>
#include <stdlib.h>
#include "spinapi.h"
#include "malloc.h"
#include <string.h>
#include <math.h>
#define PBESRPRO

/*
*������� ����������� ������ ��������
*@a,b - ����� ����� ������� ������ ���
*@return - ���
*/

int NOD(int a, int b)
{

	if (a == 0)
		return b;
	if (b == 0)
		return a;
	if (a == b)
		return a;
	if (a > b)
		return NOD(a - b, b);
	return NOD(a, b - a);
}

/*
* ������� �������� 3-� ������� ������� Data ��� ���������� �������� � ������� setPB()
* ������ [N_Channels, [Channel, N_Pulses, [T_start], [T_end]], ...]
* N_Channels - ���������� �������������� �������.
* ������� �� 4 ��������� � ���������� N_channels ����:
* 1. Channel - ����� ������
* 2. N_Pulses - ���������� ��������� � ������
* 3. ������ ������ ������ ���������
* 4. ������ ������ ����� ���������
* ������ ����������� � ������� �������� ������ ����. ������� ���� ������������ �������� ������ � ����������
*
* @*str ������ � ������� ��� ���������� �������
* @return ***Data - ������� ��������� �� ������
*/

__declspec(dllexport) int*** StrBuild(char* str) {
	int*** Data;
	char* tok;
	/*�������� �� ����������*/
	tok = strtok(str, "_");
	if (tok == NULL) {
		//printf("Error: Can't split string\nPress any key to coninue:\n");
		getchar();
		return NULL;
	}
	/*�������� ���������� �������*/
	Data = malloc(sizeof(int**) * (atoi(tok) + 1));
	if (Data == NULL) {
		//printf("Error:Can't make Data\n Press any key to continue:\n");
		getchar();
		return NULL;
	}
	/*������ �������� �������� [0][0][0], ����� ������� �������*/
	Data[0] = malloc(sizeof(int*));
	if (Data[0] == NULL) {
		//printf("Error:Can't make Data[0]\n Press any key to continue:\n");
		getchar();
		return NULL;
	}
	Data[0][0] = malloc(sizeof(int));
	if (Data[0][0] == NULL) {
		//printf("Error:Can't make Data[0][0]\n Press any key to continue:\n");
		getchar();
		return NULL;
	}
	Data[0][0][0] = atoi(tok);
	/*����� �������� �������� [0][0][0]*/
	/*������ ����� ���������� �������� Data[i]*/
	for (int i = 1; i <= Data[0][0][0]; i++) {
		tok = strtok(0, "_");
		if (tok == NULL) {
			//printf("Error: Can't split string\nPress any key to coninue:\n");
			getchar();
			return NULL;
		}
		Data[i] = malloc(sizeof(int*) * 4);
		if (Data[i] == NULL) {
			//printf("Error:Can't make Data[%d]\n Press any key to continue:\n",i);
			getchar();
			return NULL;
		}
		/*������ �������� � ���������� �������� Data[i][0][0]*/
		Data[i][0] = malloc(sizeof(int));
		if (Data[i][0] == NULL) {
			//printf("Error:Can't make Data[%d][0]\n Press any key to continue:\n",i);
			getchar();
			return NULL;
		}
		Data[i][0][0] = atoi(tok);
		/*����� �������� � ���������� �������� Data[i][0][0]*/
		/*������ �������� � ���������� �������� Data[i][1][0]*/
		tok = strtok(0, "_");
		if (tok == NULL) {
			//printf("Error: Can't split string\nPress any key to coninue:\n");
			getchar();
			return NULL;
		}
		Data[i][1] = malloc(sizeof(int));
		if (Data[i][1] == NULL) {
			//printf("Error:Can't make Data[%d][1]\n Press any key to continue:\n", i);
			getchar();
			return NULL;
		}
		Data[i][1][0] = atoi(tok);
		/*����� �������� � ���������� �������� Data[i][0][0]*/
		/*�������� ��������� Data[i][2] Data[i][3]*/
		Data[i][2] = malloc(sizeof(int) * Data[i][1][0]);
		if (Data[i][2] == NULL) {
			//printf("Error:Can't make Data[%d][2]\n Press any key to continue:\n", i);
			getchar();
			return NULL;
		}
		Data[i][3] = malloc(sizeof(int) * Data[i][1][0]);
		if (Data[i][3] == NULL) {
			//printf("Error:Can't make Data[%d][3]\n Press any key to continue:\n", i);
			getchar();
			return NULL;
		}
		/*������ ���������� �������� Data[i][2]*/
		for (int k = 0; k < Data[i][1][0]; k++) {
			tok = strtok(0, "_");
			if (tok == NULL) {
				//printf("Error: Can't split string\nPress any key to coninue:\n");
				getchar();
				return NULL;
			}
			Data[i][2][k] = atoi(tok);
		}
		/*����� ���������� �������� Data[i][2]*/
		/*������ ���������� �������� Data[i][3]*/
		for (int k = 0; k < Data[i][1][0]; k++) {
			tok = strtok(0, "_");
			if (tok == NULL) {
				//printf("Error: Can't split string\nPress any key to coninue:\n");
				getchar();
				return NULL;
			}
			Data[i][3][k] = atoi(tok);
		}
		/*����� ���������� �������� Data[i][2]*/
	}
	/*����� ����� ���������� �������� Data[i]*/
	//printf("Number of channels:%d\n Pockets:\n", Data[0][0][0]);
	for (int i = 1; i <= Data[0][0][0]; i++) {
		//printf("__%d\nAcctive channel: %d,  Number of pulses: %d	", i, Data[i][0][0], Data[i][1][0]);
		for (int g = 0; g < Data[i][1][0]; g++) {
			//printf("Impulse %d: %d___%d		", g, Data[i][2][g], Data[i][3][g]);
		}
		//printf("\n");
	}
	return Data;
}

/*������� �������. �� ��� �������� � DLL*/

int check_pb() {
	if (pb_init() != 0) {
		return -1;
	}
	else {
		pb_close();
		return 0;
	}
}

/*
* ������� �������� 3-� ������� ������� Data ��� ���������� �������� � ������� setPB()
* ������ [N_Channels, [Channel, N_Pulses, [T_start], [T_end]], ...]
* N_Channels - ���������� �������������� �������.
* ������� �� 4 ��������� � ���������� N_channels ����:
* 1. Channel - ����� ������
* 2. N_Pulses - ���������� ��������� � ������
* 3. ������ ������ ������ ���������
* 4. ������ ������ ����� ���������
*
* ���� ������ ������
* @return ***Data - ������� ��������� �� ������
*/
__declspec(dllexport) int*** Build(void) {

	int N_Channels;
	int*** Data;
	//printf("Number of active channels:");
	scanf("%d", &N_Channels);
	Data = malloc(sizeof(int**) * (N_Channels + 1));
	if (Data == NULL) {
		return -1;
	}
	Data[0] = malloc(sizeof(int*));
	if (Data[0] == NULL) {
		return -1;
	}
	Data[0][0] = malloc(sizeof(int));
	if (Data[0][0] == NULL) {
		return -1;
	}
	Data[0][0][0] = N_Channels;
	for (int i = 1; i <= N_Channels; i++) {
		Data[i] = malloc(sizeof(int*) * 4); //��������� ������
		for (int g = 0; g < 2; g++) {
			Data[i][g] = malloc(sizeof(int));	//�������� 0 � 1 ��������
		}
		//printf("Number of active channel:	");
		scanf("%d", &Data[i][0][0]);						//���������� 0 ��������
		//printf("Number of pulses in channel %d:	", *Data[i][0]);
		scanf("%d", &Data[i][1][0]);						//���������� 1 ��������
		for (int g = 2; g < 4; g++) {
			Data[i][g] = malloc(sizeof(int) * Data[i][1][0]); //�������� 2 � 3 ���������
		}
		for (int g = 0; g < Data[i][1][0]; g++) {
			//printf("%d pulse start/stop:	", g + 1);
			scanf("%d%d", &Data[i][2][g], &Data[i][3][g]);
		}
	}
	//printf("Number of channels:%d\n Pockets:\n", Data[0][0][0]);
	for (int i = 1; i <= Data[0][0][0]; i++) {
		//printf("__%d\nAcctive channel: %d,  Number of pulses: %d	", i, Data[i][0][0], Data[i][1][0]);
		for (int g = 0; g < Data[i][1][0]; g++) {
			//printf("Impulse %d: %d___%d		", g, Data[i][2][g], Data[i][3][g]);
		}
		//printf("\n");
	}
	return Data;
}

/*
* comp - ������� ��������� ��� ����������.
* ���������: ��� ��������� �� int (arg1, arg2).
* ����������: ������� �������� (*arg1 - *arg2).
* ��������: ������������ � qsort ��� ���������� ������� �� �����������.
*/
int comp(const int* arg1, const int* arg2) {
	return (*arg1 - *arg2);
}

/*
* ���������� � ����� ������������� ��������, �� ������ �� (���������� ��� ������ free())
*
* @*arr - ��������� �� ������
* @*size - ��������� �� ������ �������
*
* @return ������ ��� ��������� ����������
*/
int deleteRepeat(int* arr, int* size) {
	for (int i = 1; i < *size; i++) {
		if (arr[i] == arr[i - 1]) {
			int skip = i;
			int buf;
			while (skip < *size - 1) {
				buf = arr[skip];
				arr[skip] = arr[skip + 1];
				arr[skip + 1] = buf;
				skip++;
			}
			(*size)--;
			//printf("---\n");
		}

	}
	return 1;
}

/*
* ���������� � ����� 0 ������� �������, ��� �� ������ ���. ��������� ������ �������
*
* @*arr - ��������� �� ������
* @*size - ��������� �� ������ �������
*
* @return ��� ��������� ����������
*/
int del(int* arr, int* size) {
	int buf;
	for (int i = 0; i < (*size) - 1; i++) {
		buf = arr[i];
		arr[i] = arr[i + 1];
		arr[i + 1] = buf;
	}
	return 0;
}

/*
* ������� �������� � ����� ���������� ������������������ � �������
* @***Data - 3� ������ ������ �������� ���������� ������������������
* @repeat - ����� ����� ������ � ������� ������ ���������� ���������� ������������������
* @pulseTime, repTime - ��������� ��������� �������. 1 - ns, 1e3 - us, 1e6 - ms, 1e9 - ns
* @return 0 - �������� ����. -1 - ������
*/
__declspec(dllexport) int setPb(int*** Data, int repeat, int pulseTime, int repTime) {
	int Time_count = 0;
	int* Time;
	for (int i = 1; i <= Data[0][0][0]; i++) {
		Time_count += Data[i][1][0] * 2;
	}
	Time = malloc(sizeof(int) * Time_count);
	if (Time == NULL) {
		return -1;
	}
	int check = 0;
	for (int g = 1; g <= Data[0][0][0]; g++) {
		for (int f = 0; f < Data[g][1][0]; f++) {
			Time[check++] = Data[g][2][f];
			Time[check++] = Data[g][3][f];
		}
	}
	qsort(Time, Time_count, sizeof(int), comp);

	deleteRepeat(Time, &Time_count);
	//printf("Time mass:\n");
	//printf("Time_Count#:%d\n", Time_count);/*Debug*/
	for (int i = 0; i < Time_count; i++) {
		//	//printf("%d_%d ", i, Time[i]);
	}
	//printf("\n");
	/*�������� �������� � ������*/
	if (pb_init() != 0) {
		//printf("No board");
		free(Time);
		return -1;
	}
	pb_core_clock(500);
	pb_start_programming(PULSE_PROGRAM);
	//printf("Time_Count:%d\n", Time_count);
	for (int i = 0; i < Time_count; i++) {
		//printf("Cycle Time: %d ***************************************************************************\n", i);
		//printf("Time of cycle: %d\n", Time[i]);
		int byteVar = 0b0;
		for (int N_chan = 1; N_chan <= Data[0][0][0]; N_chan++) {
			if (Data[N_chan][1][0] == 0) {
				continue;
			}
			//printf("Channel: %d_______________\n", Data[N_chan][0][0]);
			if (Data[N_chan][2][0] == Time[i]) {
				byteVar = byteVar | (1 << Data[N_chan][0][0]);
				//printf("#1 OP\n");
				del(Data[N_chan][2], &Data[N_chan][1][0]);
				//printf("1<<%d first\n", Data[N_chan][0][0]);
			}
			else if (Data[N_chan][3][0] == Time[i]) {
				//printf("#2 OP\n");
				del(Data[N_chan][3], &Data[N_chan][1][0]);
			}
			else if ((Data[N_chan][3][0] > Time[i]) & (i != Time_count - 1) & (Data[N_chan][2][Data[N_chan][1][0] - 1] < Time[i]) & (Data[N_chan][2][0] <= Time[i])) {
				byteVar = byteVar | (1 << Data[N_chan][0][0]);
				//printf("#3 OP\n1<<%d\n", Data[N_chan][0][0]);
			}
		}
		/*//printf("byteVar now: %d\n", byteVar);*/
		if (i == Time_count - 1) {
			pb_inst(byteVar, BRANCH, 0, repTime * repeat);
			//printf("___Byte is:%d\n__Time is:%d\n", byteVar, repeat);
			//printf("BRANCH\n");
		}
		else {
			pb_inst(byteVar, CONTINUE, 0, pulseTime * (Time[i + 1] - Time[i]));
			//printf("___Byte is:%d\n__Time is:%d\n", byteVar, Time[i + 1] - Time[i]);

		/*	//printf("Out time in cycle %d: %d\n", i, (Time[i + 1] - Time[i]));*/
			//printf("Continue\n");
		}

	}
	free(Time);
	//printf("Done\n"); /*debug*/
	pb_stop_programming();
	pb_reset();
	pb_start();
	pb_close();

	return 0;
}

/*
* ������� �������� PWM �������������������. �� ������������. ����� ���� �������, ���� ��������� ������������
* 
* ������ ��������� ������ ��� ������� setPb, ������������ ����� ������ ������� ��� �������������� ��� ���������
* @int N - ����� ������� �������
* @int arr[][4] - ������ ������������� [][0] - ����� �������� ������ [0][1] - ������, [0][2] ���� ���������� � %, [0][3] ����� ����.
* @int time - ������������ ������� ms, us, ns
*
*/
__declspec(dllexport) int pb_PWM(int N, int arr[][4], int time) {
	int t = 0;
	int d;
	int tind;
	int delay = 0;
	for (int i = 0; i < N; i++) {
		//printf("cycle:%d\n", i);
		if (t < arr[i][1]) {
			t = arr[i][1];
			tind = i;
		}
	}
	float buf = t / arr[0][1];
	d = NOD(rint(buf * 100.0), 100);
	/*���������� ����� ��� ��� ���� �������� T[i]/t, ��������� ������, ��� ���������*/
	for (int i = 0; i < N; i++) {
		//printf("Devide:%d\n", arr[i][1]);
		buf = t / arr[i][1];
		d = NOD(d, rint(buf * 100)); /*���������� ����� ��������*/
	}
	//printf("NOD is:%d\n", d);
	/*������ ���� ��������� ��������� Data, �� ��� ������ ��� �������� ���� �������*/
	int*** Data;
	Data = malloc(sizeof(int**) * (N + 1));
	if (Data == NULL) {
		return NULL;
	}
	Data[0] = malloc(sizeof(int*));
	if (Data[0] == NULL) {
		return NULL;
	}
	Data[0][0] = malloc(sizeof(int));
	if (Data[0][0] == NULL) {
		return NULL;
	}
	Data[0][0][0] = N; /*����� ������� �������*/
	/*�������� ���������� ��������� �������*/
	for (int i = 1; i <= N; i++) {
		Data[i] = malloc(sizeof(int*) * 4);
		if (Data[i] == NULL) {
			return NULL;
		}
		Data[i][0] = malloc(sizeof(int));
		if (Data[i][0] == NULL) {
			return NULL;
		}
		/*����� �������� ������*/
		Data[i][0][0] = arr[i - 1][0];
		Data[i][1] = malloc(sizeof(int));
		if (Data[i][1] == NULL) {
			return NULL;
		}
		if (t == arr[i - 1][1]) {
			/*����� ��������� � ������*/
			Data[i][1][0] = rint(100.0 / d);
		}
		else {
			/*����� ��������� � ������*/
			buf = t / arr[i - 1][1];
			Data[i][1][0] = rint(buf * 100.0 / d);
		}
		Data[i][2] = malloc(sizeof(int) * Data[i][1][0]);
		Data[i][3] = malloc(sizeof(int) * Data[i][1][0]);
		if (Data[i][2] == NULL || Data[i][3] == NULL) {
			return NULL;
		}
		//printf("Config channel: %d ______________________________________________________________________________\n", Data[i][0][0]);
		//printf("Pulses in this channel: %d\n", Data[i][1][0]);
		for (int g = 0; g < Data[i][1][0]; g++) {

			/*��������� ����� ������� ��������*/
			Data[i][2][g] = arr[i - 1][3] * (g + 1) + arr[i - 1][1] * g;
			Data[i][3][g] = Data[i][2][g] + (int)rint(arr[i - 1][1] * arr[i - 1][2] / 100.0);
			if (delay < Data[i][3][g]) {
				delay = Data[i][3][g];
			}
			////printf("Time in Data[i][2][%d]:%d\nTime in Data[i][3][%d]:%d\n\n",g, Data[i][2][g],g,Data[i][3][g]);
		}

	}
	//printf("Data[0][0][0]:%d\nData[1][0][0]:%d\nData[1][1][0]:%d\n", Data[0][0][0], Data[1][0][0], Data[1][1][0]); /*Debug*/
	//printf("Start setPb******************************************************************************************\n");
	setPb(Data, t - delay, time, time);
	return 0;
}

/*
* ������� �������� � ����� ���������� ������������������ ��� �������
* @***Data - 3� ������ ������ �������� ���������� ������������������
* @repeat - ����� ����� ������ � ������� ������ ���������� ���������� ������������������
* @pulseTime, repTime - ��������� ��������� �������. 1 - ns, 1e3 - us, 1e6 - ms, 1e9 - ns
* @return 0 - �������� ����. -1 - ������
*/
__declspec(dllexport) int setPb_cold(int*** Data, int repeat, int pulseTime, int repTime) {
	int Time_count = 0;
	int* Time;
	for (int i = 1; i <= Data[0][0][0]; i++) {
		Time_count += Data[i][1][0] * 2;
	}
	Time = malloc(sizeof(int) * Time_count);
	if (Time == NULL) {
		return -1;
	}
	int check = 0;
	for (int g = 1; g <= Data[0][0][0]; g++) {
		for (int f = 0; f < Data[g][1][0]; f++) {
			Time[check++] = Data[g][2][f];
			Time[check++] = Data[g][3][f];
		}
	}
	qsort(Time, Time_count, sizeof(int), comp);

	deleteRepeat(Time, &Time_count);
	//	//printf("Time mass:\n");
		//printf("Time_Count#:%d\n", Time_count);/*Debug*/
	for (int i = 0; i < Time_count; i++) {
		//	//printf("%d_%d ", i, Time[i]);
	}
	//printf("\n");
	/*�������� �������� � ������*/
	if (pb_init() != 0) {
		//	//printf("No board");
		free(Time);
		return -1;
	}
	pb_core_clock(500);
	pb_start_programming(PULSE_PROGRAM);
	//printf("Time_Count:%d\n", Time_count);
	for (int i = 0; i < Time_count; i++) {
		//printf("Cycle Time: %d ***************************************************************************\n", i);
		//printf("Time of cycle: %d\n", Time[i]);
		int byteVar = 0b0;
		for (int N_chan = 1; N_chan <= Data[0][0][0]; N_chan++) {
			if (Data[N_chan][1][0] == 0) {
				continue;
			}
			//printf("Channel: %d_______________\n", Data[N_chan][0][0]);
			if (Data[N_chan][2][0] == Time[i]) {
				byteVar = byteVar | (1 << Data[N_chan][0][0]);
				//	//printf("#1 OP\n");
				del(Data[N_chan][2], &Data[N_chan][1][0]);
				//	//printf("1<<%d first\n", Data[N_chan][0][0]);
			}
			else if (Data[N_chan][3][0] == Time[i]) {
				//	//printf("#2 OP\n");
				del(Data[N_chan][3], &Data[N_chan][1][0]);
			}
			else if ((Data[N_chan][3][0] > Time[i]) & (i != Time_count - 1) & (Data[N_chan][2][Data[N_chan][1][0] - 1] < Time[i]) & (Data[N_chan][2][0] <= Time[i])) {
				byteVar = byteVar | (1 << Data[N_chan][0][0]);
				//	//printf("#3 OP\n1<<%d\n", Data[N_chan][0][0]);
			}
		}
		/*//printf("byteVar now: %d\n", byteVar);*/
		if (i == Time_count - 1) {
			pb_inst(byteVar, BRANCH, 0, repTime * repeat);
			//	//printf("___Byte is:%d\n__Time is:%d\n", byteVar, repeat);
			//	//printf("BRANCH\n");
		}
		else {
			pb_inst(byteVar, CONTINUE, 0, pulseTime * (Time[i + 1] - Time[i]));
			//	//printf("___Byte is:%d\n__Time is:%d\n", byteVar, Time[i + 1] - Time[i]);

				/*	//printf("Out time in cycle %d: %d\n", i, (Time[i + 1] - Time[i]));*/
			//	//printf("Continue\n");
		}

	}
	free(Time);
	//printf("Done\n"); /*debug*/
	pb_stop_programming();
	pb_reset();

	return 0;
}

/*
* ������� �������� (�������������) � ������ �����
* @return 0 - �����, -1 - ������
*/
__declspec(dllexport) int pb_Istart(void) {
	if (pb_init() != 0) {
		return -1;
	}
	pb_core_clock(500);
	pb_start();
	pb_close();
	return 0;
}

/*
* ������� �������� (�������������) � ��������� �����
* @return 0 - �����, -1 - ������
*/
__declspec(dllexport) int pb_Istop(void) {
	if (pb_init() != 0) {
		return -1;
	}
	pb_core_clock(500);
	pb_reset();
	pb_close();
	return 0;
}

/*
* ������� �������� (������������� �����)
* @return 0 - �����, -1 - ������
*/
__declspec(dllexport) int pb_I(void) {
	if (pb_init() != 0) {
		return -1;
	}
	pb_core_clock(500);
	return 0;
}

/*
* ������� �������� (������������� �����)
* @return 0 - �����, -1 - ������
*/
__declspec(dllexport) int pb_S(void) {
	return pb_start();
}

/*
* ������� �������� (������������� �����)
* @return 0 - �����, -1 - ������
*/
__declspec(dllexport) int pb_R(void) {
	return pb_reset();
}

/*
* ������� �������� (������������� �����)
* @return 0 - �����, -1 - ������
*/
__declspec(dllexport) int pb_C(void) {
	return pb_close();
}

int main(void) {
	/*
	int arr[2][4] = {{0, 400, 25, 0}, {1,100,50,0}};
	pb_PWM(2, arr, us);
	*/
	int arr[1][4] = { {0,50,20,0} };
	pb_PWM(1, arr, ms);
	/*
	if (check_pb() != 0) {
		//printf("No board:(\n");
		getchar();
		return -1;
	}
	//printf("All times in us!!!!\n");
	*/
	/*char s[] = "2_0_2_0_100_50_150_1_1_10_50";
	data = StrBuild(s);
	*/
	/*
	int d;
	scanf("Delay time:%d", &d);
	*/

	return 0;
}


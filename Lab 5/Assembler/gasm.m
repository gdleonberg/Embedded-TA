%%---------------------------------------------------------------
% Written by Gregory Leonberg for 332:493:02 "Embedded Systems Design"
% Fall 2017 Semester
% Converts custom GRISC ISA assembly into binary COE file
%%---------------------------------------------------------------

%%---------------------------------------------------------------
% format of input file is:
% [ignored lines]
% .data
% data segement
% .text
% text segement
%%---------------------------------------------------------------

%%---------------------------------------------------------------
% format of data segment is:
% [blank]                   OR
% // comment                OR
% * label: [type] [value] // comment
% types are str or num
% no spaces in string allowed
% [where comments are optional]
% [one operation or label per line]
% ignores whitespace
% assumes correct input, does not handle invalid assembly
% last line before .text MUST be a data statement
%%---------------------------------------------------------------

%%---------------------------------------------------------------
% format of text segment is:
% [blank]                   OR
% // comment                OR
% * opcode args // comment    OR
% * label: // comment
% [where comments are optional]
% [one operation or label per line]
% ignores whitespace
% assumes correct input, does not handle invalid assembly
%%---------------------------------------------------------------

% define opcode constants in associative array (dictonary)
ops = containers.Map;
ops('add') = '00000'; ops('sub') = '00001'; ops('sll') = '00010'; 
ops('srl') = '00011'; ops('sra') = '00100'; ops('and') = '00101';
ops('or') = '00110'; ops('xor') = '00111'; ops('slt') = '01000';
ops('sgt') = '01001'; ops('seq') = '01010'; ops('send') = '01011';
ops('recv') = '01100'; ops('jr') = '01101'; ops('wpix') = '01110';
ops('rpix') = '01111'; ops('beq') = '10000'; ops('bne') = '10001';
ops('ori') = '10010'; ops('lw') = '10011'; ops('sw') = '10100';
ops('j') = 	'11000'; ops('jal') = '11001'; ops('clrscr') = '11010';
ops('la') = '10010'; % pseudo instruction for ori with label as immediate

% define instruction type decoding in associative array (dictionary)
types = containers.Map;
types('00') = 'r';
types('01') = 'r';
types('10') = 'i';
types('11') = 'j';

% define register constants in associative array (dictionary)
regs = containers.Map;
regs('$zero') = '00000';
regs('$pc') = '00001';
regs('$ra') = '00010';
for i = 3:31    
    str = strcat('$r', num2str(i));
    regs(str) = dec2bin(i, 5);
end

% ask for path to input file
inpath = input('Please enter the path to the assembly file: ', 's');
cd(inpath);
inf = input('Please enter the input file name: ', 's');
inp = fopen(inf, 'r');

% handle output files
outpath = input('Please enter the name of the output text coe file: ', 's');
asm = fopen(outpath, 'w');
fprintf(asm, 'MEMORY_INITIALIZATION_RADIX=2;\n');
fprintf(asm, 'MEMORY_INITIALIZATION_VECTOR=\n');
outpathd = input('Please enter the name of the output data coe file: ', 's');
dat = fopen(outpathd, 'w');
fprintf(dat, 'MEMORY_INITIALIZATION_RADIX=2;\n');
fprintf(dat, 'MEMORY_INITIALIZATION_VECTOR=\n');

% cell array for lines of text
lines = cell(1);

% iterate across assembly code and strip comments and store into array
% strip lables and store addresses for labels
labels  = containers.Map();
dlabels = containers.Map();
dCounter = 0;
addressCounter = 0;

% advance to data segment
while(~strcmp(fgetl(inp), '.data'))
end

% parse data segment
templ = fgetl(inp);
while(~strcmp(templ, '.text'))
    astPos = find(templ == '*');
    if(~isempty(astPos))
        templ = templ(astPos+1:length(templ));
        commentsPos = strfind(templ, '//');
        if(size(commentsPos))
            templ = templ(1:commentsPos-1);
        end
        templ = strtrim(templ);
        
        % add current label to dict with current dCounter
        colonPos = find(templ == ':');
        dlabels(templ(1:colonPos-1)) = dec2bin(dCounter, 16);
        
        % convert data to groups of 16 bits and write to data coe
        args = textscan(templ, '%s', 'delimiter', ' ');
        dtype = args{1}{2};
        dval = args{1}{3};
        
        % convert data to binary and increment dcounter for next label
        if(strcmp(dtype, 'num'))
           binar = [dec2bin(str2num(dval), 16), ',\n'];
           dCounter = dCounter + 1;
        else
            binar = '';
            for i = 1:length(dval)
                binar = [binar, dec2bin(dval(i), 16), ',\n'];
                dCounter = dCounter + 1;
            end
                binar = [binar, '0000000000000000,\n'];
                dCounter = dCounter + 1;
        end
        
        % write binary to data coe file
        templ = fgetl(inp);
        if(strcmp(templ, '.text'))
            fprintf(dat, [binar(1:(length(binar)-3)), ';']);
        else
            fprintf(dat, binar);
        end
    
    else
        templ = fgetl(inp);
    end
end

% parse instruction segment
while ~feof(inp)
    
    % get line from file and strip comment if it exists and whitespace
    line = fgetl(inp);
    astPos = find(line == '*');
    if(~isempty(astPos))
        line = line(astPos+1:length(line));
        commentsPos = strfind(line, '//');
        if(size(commentsPos))
            line = line(1:commentsPos-1);
        end
        line = strtrim(line);

        % if not a label, increment address counter
        colonPos = find(line == ':');
        if(isempty(colonPos))
            addressCounter = addressCounter + 1;
            lines{addressCounter} = line;
        else
            labels(line(1:colonPos-1)) = dec2bin(addressCounter, 16);
        end
    end
end

% iterate across array and write convert each line, write to file
temp = size(lines);
numLines = temp(2);
for i = 1:numLines
    
    % split line into array by whitespace
    args = textscan(lines{i}, '%s', 'delimiter', ' ');
    opcode = args{1}{1};
    numArgs = size(args{1});
    numArgs = numArgs(1)-1;
    binop = ops(opcode);
    optype = types(binop(1:2));
    command = binop;
    
    % convert R-type
    if(optype == 'r')
        for j = 2:numArgs+1
            command = [command, regs(args{1}{j})]; 
        end
     
    elseif(optype == 'i')
        if(strcmp(opcode, 'la')) % la pseudo-instruction as ori
            command = [command, regs(args{1}{2}), regs('$zero'), dlabels(args{1}{3})];
        elseif(strcmp(opcode, 'lw') || strcmp(opcode, 'sw'))
            command = [command, regs(args{1}{2}), regs(args{1}{3}), dlabels(args{1}{4})];
        elseif(strcmp(opcode, 'beq') || strcmp(opcode, 'bne'))
            command = [command, regs(args{1}{2}), regs(args{1}{3}), labels(args{1}{4})];
        else
            temp =  dec2bin(str2double(args{1}{4}), 16);
            while(length(temp) < 16)
                temp = ['0', temp];
            end
            command = [command, regs(args{1}{2}), regs(args{1}{3}), temp];
        end
    
    % convert J-type
    else
        if(strcmp(opcode, 'j') || strcmp(opcode, 'jal'))
            command = [command, labels(args{1}{2})];
        else
            temp =  dec2bin(str2double(args{1}{4}), 16);
            while(length(temp) < 16)
                temp = ['0', temp];
            end
            command = [command, temp];
        end     
    end
    
    % pad command with blank 0s to right if smaller than 32 bits
    while(length(command) < 32)
                command = [command, '0'];
    end
    
    % write binary instruction to coe file
    fprintf(asm, command);
	if(i == numLines)
		fprintf(asm, ';');
	else
		fprintf(asm, ',\n');
    end
    
        
end

% close output file
fclose(inp);
fclose(asm);
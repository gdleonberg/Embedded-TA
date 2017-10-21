library IEEE;
use IEEE.std_logic_1164.all;
use ieee.numeric_std.all;

entity uart_tb is
end uart_tb;

architecture tb of uart_tb is
	
    component uart port (
	clk, en, send, rx, rst : in std_logic;
    charSend : in std_logic_vector (7 downto 0);
  	ready, tx, newChar : out std_logic;
  	charRec : out std_logic_vector (7 downto 0)
    );
    end component;
    
    type str is array (0 to 4) of std_logic_vector(7 downto 0);
    signal word : str := (x"48", x"65", x"6C", x"6C", x"6F");
    signal rst : std_logic := '0';
    signal clk, en, send, rx, ready, tx, newChar : std_logic := '0';
    signal charSend, charRec : std_logic_vector (7 downto 0) := (others => '0');

begin

	-- the sender UART
	dut: uart port map(
    	clk => clk,
        en => en,
        send => send,
        rx => tx,
        rst => rst,
        charSend => charSend,
        ready => ready,
        tx => tx,
        newChar => newChar,
        charRec => charRec);
    
    
    -- clock process @125 MHz
    process begin
    	clk <= '0';
        wait for 4 ns;
        clk <= '1';
        wait for 4 ns;
    end process;
    
    -- en process @ 125 MHz / 1085 = ~115200 Hz
    process begin
    	en <= '0';
        wait for 8680 ns;
        en <= '1';
        wait for 8 ns;
    end process;
    
    -- signal stimulation process
    process begin
    
    	rst <= '1';
        wait for 100 ns;
        rst <= '0';
        wait for 100 ns;
        
        for index in 0 to 4 loop
          wait until ready = '1' and en = '1';
          charSend <= word(index);
          send <= '1';
          wait for 200 ns;
          charSend <= (others => '0');
          send <= '0';
          wait until ready = '1' and en = '1' and newChar = '1';
          
          if charRec /= word(index) then
            report "Send/Receive MISMATCH at time: " & time'image(now) & 
            lf & "expected: " &
            integer'image(to_integer(unsigned(word(index)))) & 
            lf & "received: " & integer'image(to_integer(unsigned(charRec)))
            severity ERROR;
          end if;
          
        end loop;
        
        wait for 1000 ns;
        report "End of testbench" severity FAILURE;
        
    end process;

end tb;
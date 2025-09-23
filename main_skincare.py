from insert_data import my_user_entry
from insert_data import my_user_skin_info
from insert_data import my_ingredient_info
from insert_data import my_feedback_table
from insert_data import table1,table2,table4

a=int(input("press 1 to create tables\npress 2 to fill tables: "))


def main():
	n=int(input("Enter no. of entries u want : "))
	my_user_entry(n)
	my_user_skin_info(n)
	my_ingredient_info(n)
	my_feedback_table(n)

def create_tables():
	table1()
	table2()
	#table3()
	table4()

if a==1:
	create_tables()
else:
	main()



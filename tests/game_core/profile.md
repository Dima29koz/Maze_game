if you only need to collect turn stats run:

```bash
python bots_performance_test.py 
```

to get profiler results run:

```bash
python bots_performance_test.py --profile

# master
python bots_performance_test.py --file profile_res_12-16-2024_11-04-01  

# after replacing engine obj with same bot objs
python bots_performance_test.py --file profile_res_02-09-2025_22-27-47  

# after replacing bot objs with BotCell
python bots_performance_test.py --file profile_res_02-10-2025_21-50-13  

# after removing FieldState.current_player
python bots_performance_test.py --file profile_res_02-14-2025_18-58-16

# every turn new FieldState
python bots_performance_test.py --file profile_res_02-18-2025_00-08-57
```

def test_function(a, b, c):
    if a + b > 10 and c < 5:
        print('Sum of a and b is greater than 10, and c is less than 5')
    else:
        print('Condition not met')
    return a + b + c


x = [1, 2, 3, 4, 5]
y = {'key1': 'value1', 'key2': 'value2'}

test_function(1, 2, 3)


def my_function(x, y):
    return x + y


my_function(1, 2)

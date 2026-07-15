# They All Float Down Here

*Solution Guide*

## Overview

*They All Float Down Here* tests a player's understanding of the IEEE 754 floating-point standard and edge cases involving the conversion between JSON `number` values to the hardware implementation of floating-point values.

Players need to send pairs of test values to the server to determine what operations are being performed on the submitted values. The server then sends back the value it expects to compute from the two values, and competitors need to engineer their test values to arrive at that value.

Much of the challenge difficulty pertains to the server expecting values that are not representable within JSON `number` values: **infinity** and **NaN**. Players need to know how to combine two representable values to get to these unrepresentable values for each operation.

As a reminder, the challenge guide links [this](https://en.wikipedia.org/wiki/IEEE_754) useful reference. All server-side values are double-precision (64-bit) floating point.

For each question below, the expected result is posed as the question and a pair of valid inputs is provided along with an explanation.

## Question 1

*0b0111111111110000000000000000000000000000000000000000000000000000 (Value: inf)*

In this part, the server computes `v1 + v2`. Since it's not possible to submit an infinity value, the operation needs to be overflowed. Therefore, a valid pair of inputs for this part is `1e308`, `1e308`. The maximum representable value in double-precision floating-point is approximately `1.8e308`, which means that `2e308` becomes infinity in this representation.

Get the token with the following command:

```bash
./curl_command.sh 1 1e308 1e308
```

## Question 2

*0b0111111111111000000000000000000000000000000000000000000000000000 (Value: NaN)*

NaN in floating point can result from several operations. Reference [this](https://en.wikipedia.org/wiki/NaN#Operations_generating_NaN) for the full set of operations. The server wants to perform an operation on two user input values that results in NaN for this part. Since we can't represent the special values through JSON, quite a few of the possible operations in the listed reference are immediately ruled out. The remaining operations are `0.0/0.0`, square root of a negative number, logarithm of a negative number, or inverse sine/cosine of numbers below -1.0 or above 1.0. So now we can try out numbers in a more procedural way, by fixing one value and changing another to see how the result changes.

The signature feature of a division operation is that as the denominator approaches *0*, the total value approaches *infinity*. To do some testing, we'll use `1.0` as the first value and `0.0` as the second value. If the result was a simple division, we would get `infinity`. We don't, so let's adjust the second value in increments of `1.0`. The value gradually increases for a while, but the increase between each value is increasing. When the second value is `8.0`, the result is `0.56`. Increasing the second value to `9.0` changes the result to `1.27`, `10.0` results in `4.65`, `11.0` results in `0.82`, and then `12.0` gives `0.45`. This spike in the result's value shows that we're modifying the denominator of a division operation and we're close to the point where the total denominator approaches *0*. Additionally, because the sign does not change, that means the operation drops the sign through either an `abs` function or an even exponent.

Now that we know that the denominator seems to spike when our second value is around the range `9.0` to `11.0`, we need to find where the denominator actually reaches `0.0`. We can do this by submitting decimal values. There is some additional information revealed by the values we already have - since the result is larger when the second value is `9.0` than when it's `11.0`, this suggests that the `infinity` we're looking for is when the second value is less than `10.0` but greater than `9.0`, but still closer to `10.0` than `9.0`. Now we can just repeat the previous procedure with decrements of `0.1` from `10.0`. The result is highest at `9.8` - approximately `66.66`.

Now repeat the procedure again with smaller increments or decrements of `0.01`. The result keeps growing - with the second value at `9.79` the result is approximately `200.0`, and when it's at `9.78` the result is approximately `199.9`. Because these values are so close, we can tell that the infinity point is when this second value is about halfway between these two test values.

Trying `9.785` as the second value gives a result of `infinity` from the server. This means the numerator needs to be `0.0` for a `NaN` to result from the operation. Since the server is using the first value as the whole numerator, we can just specify the first value as `0.0` to get the `NaN` the server wants.

The server computes the value of `abs((v1 / (v2 - 9.785)))`, and we just walked through the process of finding values that work.

Get the token with the following command:

```bash
./curl_command.sh 2 0.0 9.785
```

## Question 3

*0b0111111111110000000000000000000000000000000000000000000000000000 (Value: inf)*

This part performs the first bitwise operation on the two values. The server computes `v1 << v2` on the *bits* of the input values. This means that we need to engineer floating-point inputs in such a way as to get:

`0b0011111111111000000000000000000000000000000000000000000000000000 << 0b0000000000000000000000000000000000000000000000000000000000000001`

To clarify, `v1` needs to look like the first value and then shift left so it turns into infinity. A valid pair of inputs is `1.5`, `5e-324`, which evaluate to the exact bit patterns shown.

We'll walk through finding a solution here. Like the previous question, we need to figure out the operation being performed first. As the challenge guide suggests, some of the questions are bitwise operations that would not normally be performed on floating point values, and this question is one of them. Supplying inputs initially gives some confusing results. It appears that the second value does nothing until it becomes very large, and then the operation still appears nonsensical. Instead, let's try engineering a floating point value from a string of bits. Start with the integer value `1`, corresponding to the 64-bit string `0b0000000000000000000000000000000000000000000000000000000000000001`. See the [solution_engineering.py](./solution_engineering.py) file's `int_to_float` function for an example of how to do this.

This gives us the `float` value `5e-324`. Try it for both inputs, and we get the bit pattern `0b...0010` (many zeroes omitted). Now get the floating point representation of `2` (`1e-323`) and `3` (`1.5e-323`). If we fix the first value to `5e-324` and try these values in sequence, we get the bit patterns `0b...0100` and `0b...1000`. We can try more values to confirm it, but this is a clear leftward bit shifting pattern.

Since the server tells us exactly what bit pattern it wants to result from its operation, we'll need to engineer the two values to send. We can shift its expected bit pattern rightward by 1 (`5e-324`) and find the corresponding floating point for the resulting bit pattern (`0b00111111111110...0`), which is `1.5`. This is also shown in the [solution_engineering.py](./solution_engineering.py) file.

Get the token with the following command:

```bash
./curl_command.sh 3 1.5 5e-324
```

## Question 4

*0b1111111111110000000000000000000000000000000000000000000000000000 (Value: -inf)*

This part may initially appear to be a subtraction operation, because specifying the same number for both input values results in a `0.0` server calculation. However, specifying different values quickly makes it apparent that is not the case. This part is another bitwise operation - XOR (`^` operator in code). Specifically, for each bit of one of the input values, the bit in the *same position* is compared, and the XOR of the two bits is the result in the same position of the output bit array.

The server is computing `v1 ^ v2` and wants the result of this operation to be `-inf`, specifically the bit pattern shown above. This means that the first twelve bits of each input must be *different* from each other, and the remaining bits must be *the same*. From this, we can engineer two valid inputs.

Exactly one of the values must be negative so that the operation result has a `1` in the **sign** bit, defined by the IEEE standard. Then, in order to get **infinity** instead of **NaN**, all of the **exponent** bits must be `1`, and all of the **mantissa** (sometimes called the **significand**) bits must be `0` (also defined by the standard).

Since we can't specify `inf` as an input, we can't just specify `inf` and `0.0` and be done, so we'll need to play with the bit patterns. Any bit pattern whose **exponent** bits are filled with `1`s represents a `NaN` or `inf` (or negative of either if the **sign** is also `1`). So one of the exponent bits of an input will need to be `0`, and the bit in the same position of the other input value must be `1`.

A valid pair of inputs is `-1.0`, `2.0` for this part. The bit pattern for `-1.0` is:

`0b1011111111110000000000000000000000000000000000000000000000000000` 

...and the bit pattern for `2.0` is:

`0b0100000000000000000000000000000000000000000000000000000000000000`. 

When combined with a bitwise XOR operation, it results in the expected bit pattern.

Get the token with the following command:

```bash
./curl_command.sh 4 -1.0 2.0
```

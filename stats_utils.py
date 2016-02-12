#!/usr/bin/env python
#
# [File Name Here]
#
# Author: [Your Name Here]
#
# [A Description Here]

import os
import sys
from numpy import *

def correlation_coef(list1,list2):
     """This program calculates the Spearman's correlation coefficient
     between two lists."""

     if len(list1) != len(list2):
          print "Lists are different lengths!  User is a bozo!"

     array1 = array(list1)
     array2 = array(list2)
     diffArray = array1 - array2
     diffSqArray = diffArray*diffArray

     lenArray = len(list1)
     diffSqSum = sum(diffSqArray)

     numerator = 6*diffSqSum
     denominator = lenArray*(lenArray*lenArray - 1)
     if denominator != 0:
          rho = 1 - float(numerator)/float(denominator)
     else:
          rho = 'NAN'

     # now calculate the student's t
     if rho != 'NAN':
          denomA = lenArray - 2
          numA = 1 - rho*rho
          if denomA != 0:
               denomB = sqrt(float(numA)/float(denomA))
               tValue = float(rho)/denomB
          else:
               tValue = 'NAN','NAN'
     else:
          tValue = 'NAN'
               
     return lenArray,diffSqSum,numerator,denominator,rho,tValue

def standardError(inList):

     tempStd = std(inList)
     tempSem = float(tempStd)/((len(inList))**0.5)

     return tempSem
     
def pearsonsCorrelation(startList1,startList2):

     list1,list2 = [],[]

     for n in range(0,len(startList1)):
          if str(startList1[n]) != 'nan' and str(startList2[n]) != 'nan':
               list1.append(startList1[n])
               list2.append(startList2[n])

     productList = []
     squaredList1 = []
     squaredList2 = []
     
     for n in range(0,len(list1)):
          productList.append(list1[n]*list2[n])
          squaredList1.append(list1[n]*list1[n])
          squaredList2.append(list2[n]*list2[n])

     numPoints = len(list1)
     sumList1 = sum(list1)
     sumList2 = sum(list2)
     sumList1Squared = sumList1*sumList1
     sumList2Squared = sumList2*sumList2
     sumProductList = sum(productList)
     sumSquaredList1 = sum(squaredList1)
     sumSquaredList2 = sum(squaredList2)

     numerator = numPoints*sumProductList - sumList1*sumList2
     denomPart1 = (numPoints*sumSquaredList1-sumList1Squared)**0.5
     denomPart2 = (numPoints*sumSquaredList2-sumList2Squared)**0.5

     correlationCoeff = float(numerator)/(denomPart1*denomPart2)

     return correlationCoeff

     
     

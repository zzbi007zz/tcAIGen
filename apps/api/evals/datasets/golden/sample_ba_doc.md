# User Authentication Module

Version: 1.0
Author: BA Team
Date: 2026-08-04

## Overview
This document describes the login and registration flows for the web application.

## Feature: User Registration
Source: Section 2.1

Users can create an account with email and password.

Acceptance Criteria:
- AC-R1: User can register with a valid email and password of 8-64 characters (explicit).
- AC-R2: Password must contain at least one uppercase letter and one digit (explicit).
- AC-R3: Duplicate email addresses are rejected with error "Email already registered" (explicit).
- AC-R4: Email verification link is sent after successful registration (explicit).
- AC-R5: Registration form shows inline validation messages (inferred).

## Feature: User Login
Source: Section 2.2

Registered users can log in with email and password.

Acceptance Criteria:
- AC-L1: User can log in with correct email and password (explicit).
- AC-L2: Five consecutive failed attempts lock the account for 15 minutes (explicit).
- AC-L3: "Remember me" keeps the session for 30 days (explicit).
- AC-L4: Unverified email accounts cannot log in (explicit).

## Feature: Password Reset
Source: Section 2.3

Users can reset a forgotten password via email link.

Acceptance Criteria:
- AC-P1: Reset link expires after 60 minutes (explicit).
- AC-P2: New password must differ from the previous 3 passwords (explicit).
- AC-P3: Reset with an unknown email shows a generic confirmation message (explicit).

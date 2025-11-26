Below is a **complete, engineering-practical severity segregation** of all the Klocwork MISRA C:2012 Amd2 C99 checkers you uploaded.
This classification is done **from an embedded-software + MCU SDK + ROM development viewpoint**, meaning:

* **HIGH-CRITICAL** → Can *crash firmware*, cause *undefined behavior*, *security vulnerabilities*, *memory corruption*, *wrong hardware register access*, *boot failures*, etc.
* **CRITICAL** → Serious reliability problems or silent functional errors that degrade system correctness or portability.
* **HIGH** → Strong MISRA-driven constraints that matter for maintainability, portability, and predictability.
* **MEDIUM** → Violations that usually don’t break code but harm clarity, maintainability, readability, or portability.
* **LOW** → Style, hygiene, or warnings that rarely cause system issues.

---

# ✅ **HIGH-CRITICAL SEVERITY**

### *(Memory corruption, UB, security, critical MCU malfunction risks)*

### **1. Buffer Overflows / Array Bounds**

ABV.ANY_SIZE_ARRAY
ABV.GENERAL
ABV.GENERAL.MULTIDIMENSION
ABV.ITERATOR
ABV.MEMBER
ABV.NON_ARRAY
ABV.STACK
ABV.TAINTED
ABV.UNICODE.BOUND_MAP
ABV.UNICODE.NNTS_MAP
ABV.UNKNOWN_SIZE
NNTS.MUST
NNTS.TAINTED

### **2. Use of Unvalidated Input (Taint) – Security**

SV.TAINTED.* (ALL variants)
SV.TAINTED.INJECTION
SV.TAINTED.PATH_TRAVERSAL
SV.TAINTED.SECURITY_DECISION

### **3. Memory Misuse**

FMM.MUST (Free mismatch)
FNH.MUST (Free non-heap)
FUM.GEN.MUST (Free unallocated)
MLK.MUST
MLK.RET.MUST
UNINIT.*.MUST (All MUST variants for uninitialized variables/array/heap)

### **4. Dangerous Pointer Operations**

MISRA.PTR.ARITH.2012
MISRA.PTR.ARITH.NOT_SAME.2012
MISRA.PTR.CMP.2008
MISRA.PTR.CMP.OBJECT.2008
MISRA.PTR.SUB
MISRA.PTR.SUB.OBJECT
MISRA.PTR.TO_PTR_TO_PTR
MISRA.FILE_PTR.DEREF.* (ALL variants)

### **5. Division by Zero**

DBZ.CONST
DBZ.CONST.CALL
DBZ.GENERAL
DBZ.ITERATOR
DBZ.ITERATOR.CALL

### **6. Return of Invalid Address**

LOCRET.* (returning address of local variable)

### **7. Unreachable Code (logic dead ⇒ broken state machine, ISR never reached)**

UNREACH.GEN
UNREACH.RETURN
UNREACH.ENUM

### **8. Wraparound / Overflow**

NUM.OVERFLOW.DF
MISRA.COMP.WRAPAROUND
MISRA.SHIFT.RANGE.2012

### **9. Dangerous stdlib / system calls in embedded**

MISRA.STDLIB.ABORT.2012_AMD2
MISRA.STDLIB.STDIO
MISRA.STDLIB.MEMORY
MISRA.STDLIB.SYSTEM.2012_AMD2
MISRA.STDLIB.TIME
MISRA.STDLIB.WRONGNAME.*

---

# ✅ **CRITICAL SEVERITY**

### *(Hard-to-debug logic defects, portability problems, serious misbehavior under specific MCU conditions)*

### **1. Function Result Misuse**

FUNCRET.GEN
FUNCRET.IMPLICIT
MISRA.FUNC.UNUSEDRET.2012
SV.RVT.RETVAL_NOTTESTED

### **2. Incorrect Macro Usage / Preprocessor Hazards**

MISRA.DEFINE.SHARP.*
MISRA.DEFINE.WRONGNAME.*
MISRA.EXPANSION.UNSAFE
MISRA.UNDEF.*
MISRA.USE.UNKNOWNDIR

### **3. Incorrect Essential Type Operations**

MISRA.ETYPE.* (all variants)
MISRA.STMT.COND.NOT_BOOLEAN.2012
MISRA.SWITCH.COND.BOOL.2012

### **4. Enum, struct, union incorrectness**

MISRA.ENUM.IMPLICIT.VAL.NON_UNIQUE
MISRA.INCOMPLETE.* (struct/union)
MISRA.UNION

### **5. File resource misuse**

MISRA.RESOURCES.FILE.*
RH.LEAK

### **6. Uninitialized Variables – possible**

UNINIT.*.MIGHT

### **7. Pointer Type Violations**

MISRA.CAST.*
MISRA.TYPE.RESTRICT.QUAL

### **8. Recursion**

MISRA.FUNC.RECUR

### **9. Goto misuse (breaks MCU control flow predictability)**

MISRA.GOTO.*
MISRA.BREAK_OR_GOTO.MULTIPLE

---

# ✅ **HIGH SEVERITY**

### *(Strong MISRA discipline requirements for predictable control flow, portability, and safe expressions)*

### **1. Expression Clarity & Side Effects**

MISRA.EXPR.PARENS.*
MISRA.INCR_DECR.SIDEEFF.2012
MISRA.LOGIC.SIDEEFF
MISRA.SIZEOF.SIDE_EFFECT
PORTING.VAR.EFFECTS

### **2. For-loop constraints**

MISRA.FOR.*

### **3. Identifier Uniqueness / Linkage**

MISRA.IDENT.*
MISRA.EXT.IDENT.*
MISRA.FUNC.STATIC.REDECL
MISRA.DECL.FUNC.INLINE.STATIC.2012

### **4. Type safety**

MISRA.STRCT_DEF.HIDDEN.2012
MISRA.TYPEDEF.NOT_UNIQUE.2012
MISRA.MEMB.FLEX_ARRAY.2012

### **5. Macro argument safety**

MISRA.MACRO_ARG.EXPRESSION.2012

---

# ✅ **MEDIUM SEVERITY**

### *(Maintainability, readability, coding hygiene issues)*

### **1. Unused Entities**

LV_UNUSED
VA_UNUSED.*
MISRA.UNUSED.*
LA_UNUSED

### **2. Function Parameter and Prototype Issues**

MISRA.FUNC.* (except recursion / unsafe returns which are higher)
MISRA.FUNC.UNUSEDPAR
MISRA.FUNC.NOPROT.DEF
MISRA.FUNC.VARARG

### **3. Language Restrictions**

MISRA.LANG.EXTENSIONS
MISRA.ASM.ENCAPS

### **4. String / char issues**

MISRA.STRING_LITERAL.NON_CONST
MISRA.TOKEN.L.SUFFIX.*
MISRA.TOKEN.OCTAL.INT
MISRA.TOKEN.UNTERMINATED.ESCAPE

### **5. Initializer problems**

MISRA.INIT.*

### **6. Preprocessor correctness**

MISRA.IF.*
MISRA.ELIF.*
MISRA.ENDIF.OTHERFILE
MISRA.INCGUARD

---

# ✅ **LOW SEVERITY**

### *(Style, readability, non-functional but useful cleanliness rules)*

MISRA.TOKEN.BADCOM
MISRA.TOKEN.COMMENTED.CODE
MISRA.INCL.BAD
MISRA.INCL.INSIDE
MISRA.INCL.SYMS
MISRA.INCOMPLETE.*.UNNAMED
EMENDA.*
CXX.ERRNO.* (C++-specific, benign for embedded C only)
MISRA.CHAR.TRIGRAPH (obsolete practice)
MISRA.LITERAL.UNSIGNED.SUFFIX
MISRA.DECL.ARRAY_SIZE
MISRA.PPARAM.NEEDS.CONST
MISRA.VAR.HIDDEN
EFFECT
INVARIANT_CONDITION.*

---

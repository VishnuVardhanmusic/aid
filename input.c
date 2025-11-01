/* intentionally MISRA-violating examples */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* MISRA.DEFINE.WRONGNAME.UNDERSCORE
   - Macro name uses a leading underscore and mixed case (forbidden by many MISRA naming rules). */
#define _badMacro 42

/* ABV.ANY_SIZE_ARRAY
   - Flexible array member (any-size array) in a struct (allowed by C99 but often disallowed by MISRA). */
typedef struct {
    size_t n;
    int payload[];   /* <-- flexible (unspecified) array member */
} FlexArray;

FlexArray *make_flex(size_t n)
{
    FlexArray *fa = malloc(sizeof(FlexArray) + n * sizeof(int));
    if (fa == NULL) return NULL;
    fa->n = n;
    for (size_t i = 0; i < n; ++i) fa->payload[i] = (int)i;
    return fa;
}

/* DBZ.ITERATOR
   - Loop divides by the loop iterator which is zero on the first iteration -> division by zero possible. */
void dbz_iterator(void)
{
    for (int i = 0; i < 5; ++i) {
        /* Undefined behaviour when i == 0 */
        int q = 10 / i;
        (void)q;
    }
}

/* MISRA.CAST.VOID_PTR_TO_OBJ_PTR.2012
   - Casting a void* (from malloc) directly to an object pointer type without an intermediate typed pointer. */
void cast_void_to_intptr(void)
{
    void *vp = malloc(sizeof(int) * 4);
    if (vp == NULL) return;
    int *ip = (int *)vp;    /* explicit cast from void* to int* (MISRA forbids such unchecked cast) */
    ip[0] = 123;
    free(vp);
}

/* MISRA.FILE_PTR.DEREF.RETURN.2012
   - Dereferencing/inspecting the opaque FILE object representation (implementation-defined / undefined). */
int file_ptr_deref(FILE *f)
{
    /* Cast FILE* to an integer pointer and read from it — non-portable and effectively dereferencing FILE internals */
    return *((int *)f);
}

/* MISRA.PPARAM.NEEDS.CONST
   - Parameter should be declared const but is not (function doesn't modify the data). */
size_t sloppy_strlen(char *s)    /* should be: const char *s */
{
    size_t len = 0;
    while (s[len] != '\0') {
        ++len;
    }
    return len;
}

/* NNTS.MIGHT
   - Non-null-terminated-string might occur: use of strncpy without ensuring NUL termination. */
void nnts_might(void)
{
    char small[4];
    /* copies exactly 4 bytes, leaving no space for NUL and not explicitly NUL-terminating */
    strncpy(small, "ABCDEFG", sizeof(small)); /* the result may not be null terminated */
    /* Printing or using `small` as a C string is unsafe here. */
    (void)printf("maybe-not-terminated: %s\n", small);
}

int main(void)
{
    /* Examples created but dangerous calls intentionally not executed to avoid crashing at runtime. */
    /* FlexArray usage (violates ABV.ANY_SIZE_ARRAY) */
    FlexArray *f = make_flex(3);
    if (f) {
        free(f);
    }

    /* The following functions demonstrate violations but are commented out to avoid UB at runtime:
       dbz_iterator();        // would cause division by zero
       cast_void_to_intptr(); // ok to run but shown to illustrate the cast violation
       file_ptr_deref(stdout);// undefined behaviour reading FILE internals
       nnts_might();          // may print a non-terminated string => UB when printing
    */

    /* Call the non-const-parameter function (safe) */
    char s[] = "hello";
    size_t L = sloppy_strlen(s);
    (void)printf("length (sloppy_strlen): %zu\n", L);

    /* show macro usage */
    (void)printf("_badMacro = %d\n", _badMacro);

    return 0;
}

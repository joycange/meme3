# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

INCLUDES = """
#include <openssl/crypto.h>
"""

TYPES = """
"""

FUNCTIONS = """
static int Cryptography_setup_locking(void);
static void (*Cryptography_locking_function_ptr)(int, int, const char *, int);
"""

MACROS = """
"""

CUSTOMIZATIONS = """
typedef enum CryptographyLockStatus {
    CRYPTOGRAPHY_LOCK_FAILURE = 0,
    CRYPTOGRAPHY_LOCK_ACQUIRED = 1,
    CRYPTOGRAPHY_LOCK_INTR = 2
} CryptographyLockStatus;

#if defined(_WIN32)

#include <windows.h>

typedef struct CryptographyOpaque_ThreadLock NRMUTEX, *PNRMUTEX;

BOOL InitializeNonRecursiveMutex(PNRMUTEX mutex)
{
    mutex->sem = CreateSemaphore(NULL, 1, 1, NULL);
    return !!mutex->sem;
}

VOID DeleteNonRecursiveMutex(PNRMUTEX mutex)
{
    /* No in-use check */
    CloseHandle(mutex->sem);
    mutex->sem = NULL ; /* Just in case */
}

DWORD EnterNonRecursiveMutex(PNRMUTEX mutex, DWORD milliseconds)
{
    return WaitForSingleObject(mutex->sem, milliseconds);
}

BOOL LeaveNonRecursiveMutex(PNRMUTEX mutex)
{
    return ReleaseSemaphore(mutex->sem, 1, NULL);
}

int CryptographyThreadLockInit (struct CryptographyOpaque_ThreadLock *lock)
{
  return InitializeNonRecursiveMutex(lock);
}

/*
 * Return 1 on success if the lock was acquired
 *
 * and 0 if the lock was not acquired. This means a 0 is returned
 * if the lock has already been acquired by this thread!
 */
CryptographyLockStatus CryptographyThreadAcquireLock
    (struct CryptographyOpaque_ThreadLock *lock, int intr_flag)
{
    /* Fow now, intr_flag does nothing on Windows, and lock acquires are
     * uninterruptible.  */
    CryptographyLockStatus success;

    if ((lock &&
        EnterNonRecursiveMutex(lock, (DWORD)INFINITE) == WAIT_OBJECT_0)
    ) {
        success = CRYPTOGRAPHY_LOCK_ACQUIRED;
    }
    else {
        success = CRYPTOGRAPHY_LOCK_FAILURE;
    }

    return success;
}

void CryptographyThreadReleaseLock(struct CryptographyOpaque_ThreadLock *lock)
{
    if (!LeaveNonRecursiveMutex(lock))
        /* XXX complain? */;
}

#else

#include <unistd.h>
#include <pthread.h>

#define CHECK_STATUS(name) \
    if (status != 0) { \
        error = 1; \
        if (error != 0) { \
            perror(name); \
        } \
    }

#if !defined(pthread_mutexattr_default)
#  define pthread_mutexattr_default ((pthread_mutexattr_t *)NULL)
#endif

struct CryptographyOpaque_ThreadLock {
    char             locked; /* 0=unlocked, 1=locked */
    char             initialized;
    pthread_mutex_t  mut;
};

typedef struct CryptographyOpaque_ThreadLock CryptographyOpaque_ThreadLock;

int CryptographyThreadLockInit
    (struct CryptographyOpaque_ThreadLock *lock)
{
    int status, error = 0;

    lock->initialized = 0;
    lock->locked = 0;

    status = pthread_mutex_init(&lock->mut,
    pthread_mutexattr_default);
    CHECK_STATUS("pthread_mutex_init");

    if (error)
        return 0;
    lock->initialized = 1;
    return 1;
}

CryptographyLockStatus CryptographyThreadAcquireLock
    (struct CryptographyOpaque_ThreadLock *lock, int intr_flag)
{
    CryptographyLockStatus success;
    int status, error = 0;

    status = pthread_mutex_lock(&lock->mut);
    CHECK_STATUS("pthread_mutex_lock[1]");

    if (error) success = CRYPTOGRAPHY_LOCK_FAILURE;
    else success = CRYPTOGRAPHY_LOCK_ACQUIRED;

    return success;
}

void CryptographyThreadReleaseLock
    (struct CryptographyOpaque_ThreadLock *lock)
{
    int status, error = 0;

    status = pthread_mutex_unlock( &lock->mut );
    CHECK_STATUS("pthread_mutex_unlock[3]");
}

#endif

static int Cryptography_lock_count = -1;
static CryptographyOpaque_ThreadLock *Cryptography_locks = NULL;

static void Cryptography_locking_function
    (int mode, int n, const char *file, int line)
{
    if ((Cryptography_locks == NULL ||
        n < 0 ||
        n >= Cryptography_lock_count)
    ) {
        return;
    }

    if (mode & CRYPTO_LOCK) {
        CryptographyThreadAcquireLock(&Cryptography_locks[n], 1);
    } else {
        CryptographyThreadReleaseLock(&Cryptography_locks[n]);
    }
}

static void (*Cryptography_locking_function_ptr)
    (int, int, const char *, int) = Cryptography_locking_function;

static int Cryptography_setup_locking(void) {
    unsigned int i;

    Cryptography_lock_count = CRYPTO_num_locks();

    Cryptography_locks = calloc(Cryptography_lock_count,
                                sizeof(CryptographyOpaque_ThreadLock));

    if (Cryptography_locks == NULL) {
        return -1;
    }

    for (i = 0; i < Cryptography_lock_count; ++i) {
        if (CryptographyThreadLockInit(&Cryptography_locks[i]) != 1) {
            return -1;
        }
    }

    CRYPTO_set_locking_callback(Cryptography_locking_function);

    return 0;
}
"""

CONDITIONAL_NAMES = {}

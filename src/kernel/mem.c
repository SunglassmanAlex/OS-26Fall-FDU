#include <aarch64/mmu.h>
#include <common/rc.h>
#include <common/spinlock.h>
#include <driver/memlayout.h>
#include <kernel/mem.h>
// #include <kernel/printk.h>

RefCount kalloc_page_cnt;

typedef struct FreePage {
    struct FreePage *next;
} FreePage;

static FreePage *free_pages;
static SpinLock page_lock;

#define BLOCK_ALIGN 8
#define BLOCK_CLASS_COUNT (PAGE_SIZE / 2 / BLOCK_ALIGN)

typedef struct FreeBlock {
    struct FreeBlock *next;
} FreeBlock;

typedef struct BlockPage {
    u64 class_index;
} BlockPage;

static FreeBlock *free_blocks[BLOCK_CLASS_COUNT];
static SpinLock block_lock;

void kinit() {
    init_rc(&kalloc_page_cnt);
    init_spinlock(&page_lock);
    free_pages = NULL;

    init_spinlock(&block_lock);

    for (int i = 0; i < BLOCK_CLASS_COUNT; ++i) {
        free_blocks[i] = NULL;
    }

    extern char end[];
    u64 start = round_up((u64)end, PAGE_SIZE);
    u64 limit = P2K(PHYSTOP);

    for (u64 addr = start; addr + PAGE_SIZE <= limit; addr += PAGE_SIZE) {
        FreePage *page = (FreePage*)addr;
        page->next = free_pages;
        free_pages = page;
    }
}

void* kalloc_page() {
    acquire_spinlock(&page_lock);
    FreePage* page = free_pages;
    if (page != NULL) {
        free_pages = page->next;
        increment_rc(&kalloc_page_cnt);
    }
    release_spinlock(&page_lock);
    return page;
}

void kfree_page(void* p) {
    acquire_spinlock(&page_lock);

    FreePage* page = (FreePage*)p;
    page->next = free_pages;
    free_pages = page;

    decrement_rc(&kalloc_page_cnt);
    release_spinlock(&page_lock);
}

void* kalloc(unsigned long long size) {
    if (size == 0 || size > PAGE_SIZE / 2) {
        return NULL;
    }

    u64 block_size = round_up(size, BLOCK_ALIGN);
    u64 index = block_size / BLOCK_ALIGN - 1;

    acquire_spinlock(&block_lock);

    if (free_blocks[index] == NULL) {
        BlockPage* page = (BlockPage*)kalloc_page();
        if (page == NULL) {
            release_spinlock(&block_lock);
            return NULL;
        }
        page->class_index = index;

        u64 start = (u64)page + sizeof(BlockPage);
        u64 limit = (u64)page + PAGE_SIZE;

        for (u64 addr = start; addr + block_size <= limit; addr += block_size) {
            FreeBlock* block = (FreeBlock*)addr;
            block->next = free_blocks[index];
            free_blocks[index] = block;
        }
    }
    FreeBlock* block = free_blocks[index];
    free_blocks[index] = block->next;

    release_spinlock(&block_lock);

    return block;
}

void kfree(void* ptr) {
    if (ptr == NULL) {
        return;
    }

    acquire_spinlock(&block_lock);

    BlockPage* page = (BlockPage*)PAGE_BASE(ptr);
    u64 index = page->class_index;

    FreeBlock* block = (FreeBlock*)ptr;
    block->next = free_blocks[index];
    free_blocks[index] = block;
    release_spinlock(&block_lock);
}

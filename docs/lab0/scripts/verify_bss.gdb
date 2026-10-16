set pagination off
set confirm off
set architecture aarch64
file build/src/kernel8.elf
target remote | qemu-system-aarch64 -machine virt,gic-version=3 -cpu cortex-a72 -smp 4 -m 4096 -display none -monitor none -serial null -global virtio-mmio.force-legacy=false -kernel build/src/kernel8.elf -gdb stdio -S
break main
continue
python
start = int(gdb.parse_and_eval("(unsigned long long)&edata"))
end = int(gdb.parse_and_eval("(unsigned long long)&end"))
length = end - start
if not 0 < length < 1048576:
    raise gdb.GdbError("Unexpected BSS range")
inferior = gdb.selected_inferior()
inferior.write_memory(start, bytes([0xa5]) * length)
before = bytes(inferior.read_memory(start, length))
if before != bytes([0xa5]) * length:
    raise gdb.GdbError("Failed to prepare BSS test bytes")
print("BSS start = 0x%016x" % start)
print("BSS end   = 0x%016x" % end)
print("BSS bytes = %d" % length)
print("Before memset: %d/%d bytes are 0xa5" % (before.count(0xa5), length))
end
disable 1
tbreak src/main.c:15
continue
python
after = bytes(gdb.selected_inferior().read_memory(start, length))
zero_count = after.count(0)
print("After memset:  %d/%d bytes are 0x00" % (zero_count, length))
if zero_count != length:
    raise gdb.GdbError("BSS clearing check failed")
print("BSS_CLEAR_CHECK: PASS")
end
kill
quit
